using System;

namespace JlSpp.Dmx
{
    /// <summary>
    /// JL_SPP DMX frames (521 bytes) and handshakes. Convention: a universe is an array
    /// of 512 bytes where index 0 is DMX channel 1.
    /// <code>
    /// [0]        0x00
    /// [1][2]     'K' 'T'          start marker (clear)
    /// [3]        scene            0 = direct control
    /// [4]        speed            0 in direct control
    /// [5..516]   512 channels     scrambled (channel 1 -> byte 5)
    /// [517]      Sin[codeNum]     )  key
    /// [518]      codeNum          )
    /// [519][520] 'T' 'K'          end marker (clear)
    /// </code>
    /// </summary>
    public static class DmxFrame
    {
        /// <summary>Bytes in one DMX frame.</summary>
        public const int FrameLength = 521;

        /// <summary>DMX channels in one universe.</summary>
        public const int UniverseSize = 512;

        /// <summary>Frame byte holding DMX channel 1.</summary>
        public const int PayloadStart = 5;

        /// <summary>Frame bytes 517 and 518 hold the key.</summary>
        public const int MarkerOffset = 517;

        /// <summary>Sending rate of the original app (one frame every 100 ms).</summary>
        public const int DefaultSendIntervalMs = 100;

        private const int EndMarkerOffset = 519;

        /// <summary>To send right after opening the port.</summary>
        public static byte[] HandshakeConnect() => new byte[] { 0xBB, 0x99, 0x77, 0x01, 0x77, 0x99 };

        /// <summary>To send right before closing the port.</summary>
        public static byte[] HandshakeDisconnect() => new byte[] { 0xBB, 0x77, 0x99, 0x10, 0x99, 0x77, 0x00, 0x55 };

        /// <summary>Builds a complete frame, ready to be written to the serial port.</summary>
        /// <param name="universe">512 bytes, index 0 = DMX channel 1.</param>
        /// <param name="codeNum">Counter 0..255, normally incremented for every frame.</param>
        /// <param name="scene">Byte 3 (0 = direct control).</param>
        /// <param name="speed">Byte 4 (0 in direct control).</param>
        public static byte[] Build(byte[] universe, byte codeNum, byte scene = 0, byte speed = 0)
        {
            CheckUniverse(universe);
            byte[] frame = BuildClearFrame(universe, scene, speed);
            Cipher.Encrypt(frame, PayloadStart, UniverseSize, codeNum, MarkerOffset);
            return frame;
        }

        /// <summary>True if the frame has the right length and the KT / TK markers.</summary>
        public static bool IsFrame(byte[] frame) =>
            frame != null && frame.Length == FrameLength &&
            frame[1] == 'K' && frame[2] == 'T' &&
            frame[EndMarkerOffset] == 'T' && frame[EndMarkerOffset + 1] == 'K';

        /// <summary>Gets the clear universe (512 bytes) back from a frame. ArgumentException if invalid.</summary>
        public static byte[] DecodeUniverse(byte[] frame, out byte codeNum)
        {
            if (!IsFrame(frame))
            {
                throw new ArgumentException("Not a valid JL_SPP DMX frame.", nameof(frame));
            }

            var copy = (byte[])frame.Clone();
            Cipher.Decrypt(copy, PayloadStart, UniverseSize, MarkerOffset);
            var universe = new byte[UniverseSize];
            Buffer.BlockCopy(copy, PayloadStart, universe, 0, UniverseSize);
            codeNum = frame[MarkerOffset + 1];
            return universe;
        }

        /// <summary>Throws unless the universe has exactly 512 bytes.</summary>
        internal static void CheckUniverse(byte[] universe)
        {
            if (universe is null || universe.Length != UniverseSize)
            {
                throw new ArgumentException($"A universe must hold {UniverseSize} bytes.", nameof(universe));
            }
        }

        /// <summary>Frame whose channels are still in clear (before scrambling).</summary>
        private static byte[] BuildClearFrame(byte[] universe, byte scene, byte speed)
        {
            var frame = new byte[FrameLength];
            frame[1] = (byte)'K';
            frame[2] = (byte)'T';
            frame[3] = scene;
            frame[4] = speed;
            Buffer.BlockCopy(universe, 0, frame, PayloadStart, UniverseSize);
            frame[EndMarkerOffset] = (byte)'T';
            frame[EndMarkerOffset + 1] = (byte)'K';
            return frame;
        }
    }
}
