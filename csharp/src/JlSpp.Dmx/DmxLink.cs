using System;
using System.Diagnostics;
using System.IO.Ports;
using System.Threading;

namespace JlSpp.Dmx
{
    /// <summary>
    /// Liaison serie avec le boitier (Bluetooth SPP vu comme un port serie : "COM6" sous
    /// Windows, "/dev/rfcomm0" sous Linux). Envoie l'univers en continu dans un thread
    /// d'arriere-plan, comme l'appli d'origine.
    /// <code>
    /// using var link = new DmxLink("COM6");
    /// link.Open();            // handshake de connexion
    /// link.Start();           // envoi continu (100 ms)
    /// link.SetChannel(1, 255);
    /// </code>
    /// </summary>
    public sealed class DmxLink : IDisposable
    {
        private readonly object _universeLock = new object();
        private readonly byte[] _universe = new byte[DmxFrame.UniverseSize];
        private readonly string _portName;
        private SerialPort? _port;
        private Thread? _thread;
        private volatile bool _running;
        private volatile int _intervalMs = DmxFrame.DefaultSendIntervalMs;
        private byte _codeNum;
        private long _framesSent;

        public DmxLink(string portName)
        {
            _portName = portName ?? throw new ArgumentNullException(nameof(portName));
        }

        /// <summary>
        /// Leve depuis le thread d'envoi si l'ecriture echoue (Bluetooth coupe...). Dans une
        /// interface graphique, repasser sur le thread de l'IHM avant d'y toucher.
        /// </summary>
        public event EventHandler<Exception>? ConnectionLost;

        public bool IsOpen => _port != null && _port.IsOpen;
        public bool IsSending => _running;
        public long FramesSent => Interlocked.Read(ref _framesSent);

        /// <summary>Intervalle entre deux trames (20 a 1000 ms ; 100 = appli d'origine).</summary>
        public int SendIntervalMs
        {
            get => _intervalMs;
            set => _intervalMs = Math.Max(20, Math.Min(1000, value));
        }

        /// <summary>channel : 1..512.</summary>
        public void SetChannel(int channel, byte value)
        {
            if (channel < 1 || channel > DmxFrame.UniverseSize)
            {
                throw new ArgumentOutOfRangeException(nameof(channel), "Un canal DMX va de 1 a 512.");
            }
            lock (_universeLock)
            {
                _universe[channel - 1] = value;
            }
        }

        /// <summary>Remplace tout l'univers (512 octets, index 0 = canal 1).</summary>
        public void SetUniverse(byte[] universe)
        {
            if (universe is null || universe.Length != DmxFrame.UniverseSize)
            {
                throw new ArgumentException("512 octets attendus.", nameof(universe));
            }
            lock (_universeLock)
            {
                Buffer.BlockCopy(universe, 0, _universe, 0, DmxFrame.UniverseSize);
            }
        }

        public byte[] Snapshot()
        {
            lock (_universeLock)
            {
                return (byte[])_universe.Clone();
            }
        }

        public void Blackout()
        {
            lock (_universeLock)
            {
                Array.Clear(_universe, 0, _universe.Length);
            }
        }

        /// <summary>Ouvre le port et envoie le handshake. Peut bloquer quelques secondes (liaison Bluetooth).</summary>
        public void Open()
        {
            if (IsOpen)
            {
                return;
            }
            var port = new SerialPort(_portName, 9600) { WriteTimeout = 2000 };
            try
            {
                port.Open();
                var hello = DmxFrame.HandshakeConnect();
                port.Write(hello, 0, hello.Length);
            }
            catch
            {
                port.Dispose();
                throw;
            }
            _port = port;
        }

        /// <summary>Envoie une trame avec l'etat actuel de l'univers.</summary>
        public void SendFrame()
        {
            var port = _port ?? throw new InvalidOperationException("Port non ouvert : appelle Open().");
            _codeNum = unchecked((byte)(_codeNum + 1));
            var frame = DmxFrame.Build(Snapshot(), _codeNum);
            port.Write(frame, 0, frame.Length);
            Interlocked.Increment(ref _framesSent);
        }

        /// <summary>Demarre l'envoi continu.</summary>
        public void Start()
        {
            if (_running)
            {
                return;
            }
            if (!IsOpen)
            {
                throw new InvalidOperationException("Port non ouvert : appelle Open().");
            }
            _running = true;
            _thread = new Thread(Loop) { IsBackground = true, Name = "JlSpp.Dmx send loop" };
            _thread.Start();
        }

        public void Stop()
        {
            _running = false;
            var thread = _thread;
            if (thread != null && thread != Thread.CurrentThread)
            {
                thread.Join(1500);
            }
            _thread = null;
        }

        /// <summary>Arret, handshake de deconnexion, fermeture.</summary>
        public void Close()
        {
            Stop();
            var port = _port;
            _port = null;
            if (port == null)
            {
                return;
            }
            try
            {
                var bye = DmxFrame.HandshakeDisconnect();
                port.Write(bye, 0, bye.Length);
            }
            catch (Exception)
            {
                // le boitier a peut-etre deja coupe la liaison
            }
            port.Dispose();
        }

        private void Loop()
        {
            var clock = Stopwatch.StartNew();
            while (_running)
            {
                long started = clock.ElapsedMilliseconds;
                try
                {
                    SendFrame();
                }
                catch (Exception ex)
                {
                    _running = false;
                    ConnectionLost?.Invoke(this, ex);
                    return;
                }
                Thread.Sleep((int)Math.Max(1, _intervalMs - (clock.ElapsedMilliseconds - started)));
            }
        }

        public void Dispose() => Close();
    }
}
