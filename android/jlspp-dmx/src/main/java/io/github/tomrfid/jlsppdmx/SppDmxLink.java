package io.github.tomrfid.jlsppdmx;

import android.Manifest;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;

import androidx.annotation.Nullable;
import androidx.annotation.RequiresPermission;

import java.io.IOException;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.UUID;

/**
 * Bluetooth SPP link to the interface, like the RY-AI app ({@code BtClient.java}):
 * RFCOMM socket on the standard SPP UUID, handshake, then one frame every 100 ms.
 *
 * <pre>
 * SppDmxLink link = new SppDmxLink(device);   // already paired BluetoothDevice ("RY-...")
 * link.connect();                             // blocking: not on the main thread
 * link.start();
 * link.setChannel(1, 255);
 * ...
 * link.close();
 * </pre>
 *
 * Android 12+: the BLUETOOTH_CONNECT permission must have been granted at runtime.
 */
public final class SppDmxLink implements AutoCloseable {

    /** Standard SPP UUID, the one used by the original app. */
    public static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private static final int MIN_INTERVAL_MS = 20;
    private static final int MAX_INTERVAL_MS = 1000;

    /** Called from the sending thread when the link is lost. */
    public interface Listener {
        void onConnectionLost(Exception error);
    }

    private final BluetoothDevice device;
    private final byte[] universe = new byte[DmxFrame.UNIVERSE_SIZE]; // index 0 = channel 1
    private final Object lock = new Object();                         // protects universe
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

    /** Delay between two frames (20..1000 ms; 100 = original app). */
    public void setSendIntervalMs(int ms) {
        intervalMs = Math.max(MIN_INTERVAL_MS, Math.min(MAX_INTERVAL_MS, ms));
    }

    // ------------------------------------------------------------------ channels

    /** Sets one channel. channel: 1..512, value: 0..255. */
    public void setChannel(int channel, int value) {
        checkChannel(channel);
        synchronized (lock) {
            universe[channel - 1] = (byte) value;
        }
    }

    /** Current value of one channel (1..512). */
    public int getChannel(int channel) {
        checkChannel(channel);
        synchronized (lock) {
            return universe[channel - 1] & 0xFF;
        }
    }

    /** Replaces the whole universe (512 bytes, index 0 = channel 1). */
    public void setUniverse(byte[] values) {
        DmxFrame.checkUniverse(values);
        synchronized (lock) {
            System.arraycopy(values, 0, universe, 0, DmxFrame.UNIVERSE_SIZE);
        }
    }

    /** Copy of the current universe. */
    public byte[] snapshot() {
        synchronized (lock) {
            return universe.clone();
        }
    }

    /** Sets every channel to 0. */
    public void blackout() {
        synchronized (lock) {
            Arrays.fill(universe, (byte) 0);
        }
    }

    // ---------------------------------------------------------------- connection

    /** Opens the RFCOMM socket and sends the handshake. BLOCKING: do not call on the UI thread. */
    @RequiresPermission(Manifest.permission.BLUETOOTH_CONNECT)
    public void connect() throws IOException {
        BluetoothSocket s = device.createRfcommSocketToServiceRecord(SPP_UUID);
        s.connect();
        socket = s;
        out = s.getOutputStream();
        write(DmxFrame.handshakeConnect());
    }

    /** Sends one frame with the current state of the universe. */
    public void sendFrame() throws IOException {
        if (out == null) {
            throw new IllegalStateException("Not connected: call connect() first");
        }
        write(DmxFrame.build(snapshot(), nextCodeNum()));
    }

    /** Starts sending frames continuously from a background thread. */
    public void start() {
        if (running) {
            return;
        }
        running = true;
        thread = new Thread(this::sendLoop, "jlspp-dmx-send");
        thread.setDaemon(true);
        thread.start();
    }

    /** Stops the background sending (the socket stays open). */
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

    /** Stops sending, sends the disconnect handshake and closes the socket. */
    @Override
    public void close() {
        stop();
        try {
            if (out != null) {
                write(DmxFrame.handshakeDisconnect());
            }
        } catch (IOException ignored) {
            // the interface may already have dropped the link
        }
        try {
            if (socket != null) {
                socket.close();
            }
        } catch (IOException ignored) {
            // nothing more to do
        }
        socket = null;
        out = null;
    }

    // ------------------------------------------------------------------ internals

    private static void checkChannel(int channel) {
        if (channel < 1 || channel > DmxFrame.UNIVERSE_SIZE) {
            throw new IllegalArgumentException("A DMX channel goes from 1 to 512");
        }
    }

    private void write(byte[] data) throws IOException {
        out.write(data);
        out.flush();
    }

    /** Counter written in each frame (any value works, the original app increments it). */
    private int nextCodeNum() {
        codeNum = (codeNum + 1) & 0xFF;
        return codeNum;
    }

    private void sendLoop() {
        long next = System.nanoTime();
        while (running) {
            try {
                sendFrame();
            } catch (Exception e) {
                running = false;
                notifyConnectionLost(e);
                return;
            }
            next += intervalMs * 1_000_000L;
            if (!sleepUntil(next)) {
                return;
            }
        }
    }

    /** Sleeps until the given System.nanoTime(); false if the thread was interrupted. */
    private static boolean sleepUntil(long nanoTime) {
        long sleepMs = Math.max(1, (nanoTime - System.nanoTime()) / 1_000_000L);
        try {
            Thread.sleep(sleepMs);
            return true;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }

    private void notifyConnectionLost(Exception error) {
        Listener l = listener;
        if (l != null) {
            l.onConnectionLost(error);
        }
    }
}
