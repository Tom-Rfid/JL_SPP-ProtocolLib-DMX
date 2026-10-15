using System;
using System.Diagnostics;
using System.IO.Ports;
using System.Threading;

namespace JlSpp.Dmx
{
    /// <summary>
    /// Serial link to the interface (Bluetooth SPP seen as a serial port: "COM6" on
    /// Windows, "/dev/rfcomm0" on Linux). Keeps sending the universe from a background
    /// thread, like the original app.
    /// <code>
    /// using var link = new DmxLink("COM6");
    /// link.Open();            // connect handshake
    /// link.Start();           // continuous sending (100 ms)
    /// link.SetChannel(1, 255);
    /// </code>
    /// </summary>
    public sealed class DmxLink : IDisposable
    {
        private const int MinIntervalMs = 20;
        private const int MaxIntervalMs = 1000;

        private readonly object _universeLock = new object(); // protects _universe
        private readonly byte[] _universe = new byte[DmxFrame.UniverseSize]; // index 0 = channel 1
        private readonly string _portName;
        private SerialPort? _port;
        private Thread? _thread;
        private volatile bool _running;
        private volatile int _intervalMs = DmxFrame.DefaultSendIntervalMs;
        private byte _codeNum;
        private long _framesSent;

        /// <param name="portName">"COM6", "/dev/rfcomm0"...</param>
        public DmxLink(string portName)
        {
            _portName = portName ?? throw new ArgumentNullException(nameof(portName));
        }

        /// <summary>
        /// Raised from the sending thread if a write fails (Bluetooth dropped...). In a GUI,
        /// switch back to the UI thread before touching controls.
        /// </summary>
        public event EventHandler<Exception>? ConnectionLost;

        /// <summary>True once <see cref="Open"/> succeeded.</summary>
        public bool IsOpen => _port != null && _port.IsOpen;

        /// <summary>True while the background thread sends frames.</summary>
        public bool IsSending => _running;

        /// <summary>Number of frames sent since the creation of the link.</summary>
        public long FramesSent => Interlocked.Read(ref _framesSent);

        /// <summary>Delay between two frames (20..1000 ms; 100 = original app).</summary>
        public int SendIntervalMs
        {
            get => _intervalMs;
            set => _intervalMs = Math.Max(MinIntervalMs, Math.Min(MaxIntervalMs, value));
        }

        // ------------------------------------------------------------------ channels

        /// <summary>Sets one channel (1..512).</summary>
        public void SetChannel(int channel, byte value)
        {
            CheckChannel(channel);
            lock (_universeLock)
            {
                _universe[channel - 1] = value;
            }
        }

        /// <summary>Current value of one channel (1..512).</summary>
        public byte GetChannel(int channel)
        {
            CheckChannel(channel);
            lock (_universeLock)
            {
                return _universe[channel - 1];
            }
        }

        /// <summary>Replaces the whole universe (512 bytes, index 0 = channel 1).</summary>
        public void SetUniverse(byte[] universe)
        {
            DmxFrame.CheckUniverse(universe);
            lock (_universeLock)
            {
                Buffer.BlockCopy(universe, 0, _universe, 0, DmxFrame.UniverseSize);
            }
        }

        /// <summary>Copy of the current universe.</summary>
        public byte[] Snapshot()
        {
            lock (_universeLock)
            {
                return (byte[])_universe.Clone();
            }
        }

        /// <summary>Sets every channel to 0.</summary>
        public void Blackout()
        {
            lock (_universeLock)
            {
                Array.Clear(_universe, 0, _universe.Length);
            }
        }

        // ---------------------------------------------------------------- connection

        /// <summary>Opens the port and sends the connect handshake. May block a few seconds (Bluetooth link).</summary>
        public void Open()
        {
            if (IsOpen)
            {
                return;
            }
            var port = new SerialPort(_portName, 9600) { WriteTimeout = 2000 }; // baud rate is irrelevant on Bluetooth
            try
            {
                port.Open();
                Write(port, DmxFrame.HandshakeConnect());
            }
            catch
            {
                port.Dispose();
                throw;
            }
            _port = port;
        }

        /// <summary>Sends one frame with the current state of the universe.</summary>
        public void SendFrame()
        {
            var port = _port ?? throw new InvalidOperationException("Port not open: call Open() first.");
            Write(port, DmxFrame.Build(Snapshot(), NextCodeNum()));
            Interlocked.Increment(ref _framesSent);
        }

        /// <summary>Starts sending frames continuously from a background thread.</summary>
        public void Start()
        {
            if (_running)
            {
                return;
            }
            if (!IsOpen)
            {
                throw new InvalidOperationException("Port not open: call Open() first.");
            }
            _running = true;
            _thread = new Thread(SendLoop) { IsBackground = true, Name = "JlSpp.Dmx send loop" };
            _thread.Start();
        }

        /// <summary>Stops the background sending (the port stays open).</summary>
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

        /// <summary>Stops sending, sends the disconnect handshake and closes the port.</summary>
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
                Write(port, DmxFrame.HandshakeDisconnect());
            }
            catch (Exception)
            {
                // the interface may already have dropped the link
            }
            port.Dispose();
        }

        /// <summary>Same as <see cref="Close"/>.</summary>
        public void Dispose() => Close();

        // ------------------------------------------------------------------ internals

        private static void CheckChannel(int channel)
        {
            if (channel < 1 || channel > DmxFrame.UniverseSize)
            {
                throw new ArgumentOutOfRangeException(nameof(channel), "A DMX channel goes from 1 to 512.");
            }
        }

        private static void Write(SerialPort port, byte[] data) => port.Write(data, 0, data.Length);

        /// <summary>Counter written in each frame (any value works, the original app increments it).</summary>
        private byte NextCodeNum()
        {
            _codeNum = unchecked((byte)(_codeNum + 1));
            return _codeNum;
        }

        private void SendLoop()
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
                long elapsed = clock.ElapsedMilliseconds - started;
                Thread.Sleep((int)Math.Max(1, _intervalMs - elapsed));
            }
        }
    }
}
