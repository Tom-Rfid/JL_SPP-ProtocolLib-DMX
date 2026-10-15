package io.github.tomrfid.jlsppdmx;

import android.Manifest;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;

import androidx.annotation.Nullable;
import androidx.annotation.RequiresPermission;

import java.io.IOException;
import java.io.OutputStream;
import java.util.UUID;

/**
 * Liaison Bluetooth SPP avec le boitier, comme l'appli RY-AI ({@code BtClient.java}) :
 * socket RFCOMM sur l'UUID SPP standard, handshake, puis une trame toutes les 100 ms.
 *
 * <pre>
 * SppDmxLink link = new SppDmxLink(device);   // BluetoothDevice deja appaire ("RY-...")
 * link.connect();                             // bloquant : hors du thread principal
 * link.start();
 * link.setChannel(1, 255);
 * ...
 * link.close();
 * </pre>
 *
 * Android 12+ : la permission BLUETOOTH_CONNECT doit avoir ete accordee a l'execution.
 */
public final class SppDmxLink implements AutoCloseable {

    /** UUID SPP standard, celui utilise par l'appli d'origine. */
    public static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    /** Appele depuis le thread d'envoi quand la liaison est perdue. */
    public interface Listener {
        void onConnectionLost(Exception error);
    }

    private final BluetoothDevice device;
    private final byte[] universe = new byte[DmxFrame.UNIVERSE_SIZE];
    private final Object lock = new Object();
    private BluetoothSocket socket;
    private OutputStream out;
    private Thread thread;
    private volatile boolean running;
    private volatile int intervalMs = DmxFrame.DEFAULT_SEND_INTERVAL_MS;
    private int codeNum;
    @Nullable private volatile Listener listener;

    public SppDmxLink(BluetoothDevice device) {
        this.device = device;
    }

    public void setListener(@Nullable Listener listener) {
        this.listener = listener;
    }

    public void setSendIntervalMs(int ms) {
        intervalMs = Math.max(20, Math.min(1000, ms));
    }

    /** channel : 1..512, value : 0..255. */
    public void setChannel(int channel, int value) {
        if (channel < 1 || channel > DmxFrame.UNIVERSE_SIZE) {
            throw new IllegalArgumentException("Un canal DMX va de 1 a 512");
        }
        synchronized (lock) {
            universe[channel - 1] = (byte) value;
        }
    }

    /** Remplace tout l'univers (512 octets, index 0 = canal 1). */
    public void setUniverse(byte[] values) {
        synchronized (lock) {
            System.arraycopy(values, 0, universe, 0, DmxFrame.UNIVERSE_SIZE);
        }
    }

    public void blackout() {
        synchronized (lock) {
            java.util.Arrays.fill(universe, (byte) 0);
        }
    }

    /** Ouvre la socket RFCOMM et envoie le handshake. BLOQUANT : ne pas appeler sur le thread UI. */
    @RequiresPermission(Manifest.permission.BLUETOOTH_CONNECT)
    public void connect() throws IOException {
        BluetoothSocket s = device.createRfcommSocketToServiceRecord(SPP_UUID);
        s.connect();
        socket = s;
        out = s.getOutputStream();
        out.write(DmxFrame.handshakeConnect());
        out.flush();
    }

    /** Envoie une trame avec l'etat actuel de l'univers. */
    public void sendFrame() throws IOException {
        if (out == null) {
            throw new IllegalStateException("Non connecte : appelle connect()");
        }
        byte[] snapshot;
        synchronized (lock) {
            snapshot = universe.clone();
        }
        codeNum = (codeNum + 1) & 0xFF;
        out.write(DmxFrame.build(snapshot, codeNum));
        out.flush();
    }

    /** Demarre l'envoi continu dans un thread d'arriere-plan. */
    public void start() {
        if (running) {
            return;
        }
        running = true;
        thread = new Thread(this::loop, "jlspp-dmx-send");
        thread.setDaemon(true);
        thread.start();
    }

    public void stop() {
        running = false;
        Thread t = thread;
        if (t != null && t != Thread.currentThread()) {
            try {
                t.join(1500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        thread = null;
    }

    /** Arret, handshake de deconnexion, fermeture de la socket. */
    @Override
    public void close() {
        stop();
        try {
            if (out != null) {
                out.write(DmxFrame.handshakeDisconnect());
                out.flush();
            }
        } catch (IOException ignored) {
            // le boitier a peut-etre deja coupe
        }
        try {
            if (socket != null) {
                socket.close();
            }
        } catch (IOException ignored) {
            // rien a faire
        }
        socket = null;
        out = null;
    }

    private void loop() {
        long next = System.nanoTime();
        while (running) {
            try {
                sendFrame();
            } catch (Exception e) {
                running = false;
                Listener l = listener;
                if (l != null) {
                    l.onConnectionLost(e);
                }
                return;
            }
            next += intervalMs * 1_000_000L;
            long sleepMs = Math.max(1, (next - System.nanoTime()) / 1_000_000L);
            try {
                Thread.sleep(sleepMs);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }
    }
}
