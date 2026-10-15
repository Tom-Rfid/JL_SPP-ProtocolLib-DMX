package io.github.tomrfid.jlsppdmx;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.Test;

/** Tests JVM (sans appareil) contre spec/test_vectors.json. */
public class DmxFrameTest {

    private static String readSpec() throws Exception {
        File dir = new File("").getAbsoluteFile();
        while (dir != null) {
            File candidate = new File(dir, "spec/test_vectors.json");
            if (candidate.isFile()) {
                return new String(Files.readAllBytes(candidate.toPath()), StandardCharsets.UTF_8);
            }
            dir = dir.getParentFile();
        }
        throw new IllegalStateException("spec/test_vectors.json introuvable");
    }

    private static byte[] hex(String s) {
        byte[] out = new byte[s.length() / 2];
        for (int i = 0; i < out.length; i++) {
            out[i] = (byte) Integer.parseInt(s.substring(2 * i, 2 * i + 2), 16);
        }
        return out;
    }

    @Test
    public void everyVectorIsReproducedAndDecoded() throws Exception {
        // Mini-lecture du JSON (pas de dependance) : name, code_num, universe_hex, frame_hex.
        Pattern p = Pattern.compile(
                "\"name\":\\s*\"([^\"]+)\".*?\"code_num\":\\s*(\\d+).*?\"universe_hex\":\\s*\"([0-9a-f]+)\".*?\"frame_hex\":\\s*\"([0-9a-f]+)\"",
                Pattern.DOTALL);
        Matcher m = p.matcher(readSpec());
        int count = 0;
        while (m.find()) {
            String name = m.group(1);
            int code = Integer.parseInt(m.group(2));
            byte[] universe = hex(m.group(3));
            byte[] frame = hex(m.group(4));

            assertArrayEquals(name, frame, DmxFrame.build(universe, code));
            assertArrayEquals(name, universe, DmxFrame.decodeUniverse(frame));
            assertEquals(name, code, DmxFrame.codeNumOf(frame));
            count++;
        }
        assertTrue("aucun vecteur lu", count >= 6);
    }

    @Test
    public void spiderHelperShiftsByOne() {
        MindiSpider spider = new MindiSpider(1);
        assertEquals(2, spider.dmxChannel(MindiSpider.MOTOR_1));
        byte[] universe = new byte[DmxFrame.UNIVERSE_SIZE];
        spider.setWings(universe, 200, true);
        assertEquals(200, universe[1] & 0xFF);
        assertEquals(55, universe[2] & 0xFF);
    }

    @Test
    public void invalidFramesAreRejected() {
        assertFalse(DmxFrame.isFrame(new byte[DmxFrame.FRAME_LENGTH]));
    }
}
