using System;

namespace JlSpp.Dmx
{
    /// <summary>
    /// Trames DMX JL_SPP (521 octets) et poignees de main. Convention : un univers est un
    /// tableau de 512 octets dont l'index 0 correspond au canal DMX 1.
    /// <code>
    /// [0]      0x00
    /// [1][2]   'K' 'T'           marqueurs de debut (en clair)
    /// [3]      scene             0 = pilotage direct
    /// [4]      vitesse           0 en pilotage direct
    /// [5..516] 512 canaux        brouilles (canal 1 -> octet 5)
    /// [517]    Sin[codeNum]      )  cle
    /// [518]    codeNum           )
    /// [519][520] 'T' 'K'         marqueurs de fin (en clair)
    /// </code>
    /// </summary>
    public static class DmxFrame
    {
        public const int FrameLength = 521;
        public const int UniverseSize = 512;
        public const int PayloadStart = 5;
        public const int MarkerOffset = 517;

        /// <summary>Cadence d'envoi de l'appli d'origine (une trame toutes les 100 ms).</summary>
        public const int DefaultSendIntervalMs = 100;

        /// <summary>A envoyer juste apres l'ouverture du port.</summary>
        public static byte[] HandshakeConnect() => new byte[] { 0xBB, 0x99, 0x77, 0x01, 0x77, 0x99 };

        /// <summary>A envoyer juste avant la fermeture du port.</summary>
        public static byte[] HandshakeDisconnect() => new byte[] { 0xBB, 0x77, 0x99, 0x10, 0x99, 0x77, 0x00, 0x55 };

        /// <summary>Construit une trame complete, prete a etre ecrite sur le port serie.</summary>
        /// <param name="universe">512 octets, index 0 = canal DMX 1.</param>
        /// <param name="codeNum">Compteur 0..255, normalement incremente a chaque trame.</param>
        /// <param name="scene">Octet 3 (0 = pilotage direct).</param>
        /// <param name="speed">Octet 4 (0 en pilotage direct).</param>
        public static byte[] Build(byte[] universe, byte codeNum, byte scene = 0, byte speed = 0)
        {
            if (universe is null || universe.Length != UniverseSize)
            {
                throw new ArgumentException($"L'univers doit faire {UniverseSize} octets.", nameof(universe));
            }

            var frame = new byte[FrameLength];
            frame[1] = (byte)'K';
            frame[2] = (byte)'T';
            frame[3] = scene;
            frame[4] = speed;
            Buffer.BlockCopy(universe, 0, frame, PayloadStart, UniverseSize);
            frame[519] = (byte)'T';
            frame[520] = (byte)'K';
            Cipher.Encrypt(frame, PayloadStart, UniverseSize, codeNum, MarkerOffset);
            return frame;
        }

        /// <summary>true si la trame a la bonne longueur et les marqueurs KT / TK.</summary>
        public static bool IsFrame(byte[] frame) =>
            frame != null && frame.Length == FrameLength &&
            frame[1] == 'K' && frame[2] == 'T' && frame[519] == 'T' && frame[520] == 'K';

        /// <summary>Retrouve l'univers (512 octets) d'une trame. Leve ArgumentException si invalide.</summary>
        public static byte[] DecodeUniverse(byte[] frame, out byte codeNum)
        {
            if (!IsFrame(frame))
            {
                throw new ArgumentException("Ce n'est pas une trame DMX JL_SPP valide.", nameof(frame));
            }

            var copy = (byte[])frame.Clone();
            Cipher.Decrypt(copy, PayloadStart, UniverseSize, MarkerOffset);
            var universe = new byte[UniverseSize];
            Buffer.BlockCopy(copy, PayloadStart, universe, 0, UniverseSize);
            codeNum = frame[MarkerOffset + 1];
            return universe;
        }
    }
}
