namespace JlSpp.Dmx
{
    /// <summary>
    /// Brouillage JL_SPP (portage de <c>Code.java</c>, appli Android RY-AI). Substitution par
    /// table choisie selon <c>codeNum</c> : <c>table = Password[Sin[codeNum] % 5]</c>,
    /// <c>sortie = table[(octet + codeNum) % 256]</c>. Les tables sont generees depuis
    /// <c>spec/cipher_tables.json</c> (voir docs/cipher.md).
    /// </summary>
    public static class Cipher
    {
        /// <summary>
        /// Equivalent de <c>Code.Encryption1</c>, EN PLACE : brouille
        /// <c>buffer[start .. start+length-1]</c> et ecrit la cle en
        /// <c>buffer[markerOffset]</c> (= Sin[codeNum]) et <c>buffer[markerOffset+1]</c> (= codeNum).
        /// </summary>
        public static void Encrypt(byte[] buffer, int start, int length, byte codeNum, int markerOffset)
        {
            byte[] table = CipherTables.Password[CipherTables.Sin[codeNum] % 5];
            for (int i = start; i < start + length; i++)
            {
                buffer[i] = table[(byte)(buffer[i] + codeNum)];
            }
            buffer[markerOffset] = CipherTables.Sin[codeNum];
            buffer[markerOffset + 1] = codeNum;
        }

        /// <summary>Equivalent de <c>Code.Decode</c>, EN PLACE, en relisant la cle ecrite dans le buffer.</summary>
        public static void Decrypt(byte[] buffer, int start, int length, int markerOffset)
        {
            byte[] table = CipherTables.Decode[buffer[markerOffset] % 5];
            byte key = buffer[markerOffset + 1];
            for (int i = start; i < start + length; i++)
            {
                buffer[i] = (byte)(table[buffer[i]] - key);
            }
        }
    }
}
