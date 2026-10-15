namespace JlSpp.Dmx
{
    /// <summary>
    /// Channel scrambling of the JL_SPP DMX protocol (port of <c>Code.java</c>, RY-AI Android app).
    /// <para>
    /// This is NOT cryptography: a byte substitution chosen by a counter <c>codeNum</c>:
    /// <c>table = Password[Sin[codeNum] % 5]</c>, <c>output = table[(byte + codeNum) % 256]</c>.
    /// The tables are generated from <c>spec/cipher_tables.json</c> (see docs/cipher.md).
    /// </para>
    /// </summary>
    public static class Cipher
    {
        private const int TableCount = 5;

        /// <summary>
        /// Same as <c>Code.Encryption1</c>, IN PLACE: scrambles
        /// <c>buffer[start .. start+length-1]</c> and writes the key at
        /// <c>buffer[markerOffset]</c> (= Sin[codeNum]) and <c>buffer[markerOffset+1]</c> (= codeNum).
        /// </summary>
        public static void Encrypt(byte[] buffer, int start, int length, byte codeNum, int markerOffset)
        {
            byte[] table = ScrambleTable(codeNum);
            for (int i = start; i < start + length; i++)
            {
                buffer[i] = ScrambleByte(buffer[i], codeNum, table);
            }
            buffer[markerOffset] = CipherTables.Sin[codeNum];
            buffer[markerOffset + 1] = codeNum;
        }

        /// <summary>Same as <c>Code.Decode</c>, IN PLACE, reading the key back from the buffer.</summary>
        public static void Decrypt(byte[] buffer, int start, int length, int markerOffset)
        {
            byte[] table = UnscrambleTable(buffer[markerOffset]);
            byte key = buffer[markerOffset + 1];
            for (int i = start; i < start + length; i++)
            {
                buffer[i] = UnscrambleByte(buffer[i], key, table);
            }
        }

        /// <summary>Substitution table used for a given counter value.</summary>
        private static byte[] ScrambleTable(byte codeNum) => CipherTables.Password[CipherTables.Sin[codeNum] % TableCount];

        /// <summary>Inverse table, found from the Sin value written in the frame.</summary>
        private static byte[] UnscrambleTable(byte sinValue) => CipherTables.Decode[sinValue % TableCount];

        /// <summary>Shift the value by the counter, then substitute it.</summary>
        private static byte ScrambleByte(byte value, byte codeNum, byte[] table) => table[(byte)(value + codeNum)];

        /// <summary>Substitute back, then remove the counter shift.</summary>
        private static byte UnscrambleByte(byte value, byte key, byte[] table) => (byte)(table[value] - key);
    }
}
