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

/** JVM tests (no device needed) against spec/test_vectors.json. */
public class DmxFrameTest {

    /** Small JSON reading without dependency: name, code_num, universe_hex, frame_hex. */
    private static final Pattern VECTOR = Pattern.compile(
            "\"name\":\\s*\"([^\"]+)\".*?\"code_num\":\\s*(\\d+).*?\"universe_hex\":\\s*\"([0-9a-f]+)\".*?\"frame_hex\":\\s*\"([0-9a-f]+)\"",
            Pattern.DOTALL);

    /** Walks up from the working directory to spec/test_vectors.json. */
    private static String readSpec() throws Exception {
        File dir = new File("").getAbsoluteFile();
        while (dir != null) {
            File candidate = new File(dir, "spec/test_vectors.json");
            if (candidate.isFile()) {
                return new String(Files.readAllBytes(candidate.toPath()), StandardCharsets.UTF_8);
            }
            dir = dir.getParentFile();
        }
        throw new IllegalStateException("spec/test_vectors.json not found");
    }

    private static byte[] hex(String s) {
        byte[] out = new byte[s.length() / 2];
        for (int i = 0; i < out.length; i++) {
            out[i] = (byte) Integer.parseInt(s.substring(2 * i, 2 * i + 2), 16);
        }
        return out;
    }

    /** Universe of the test vector called name. */
    private static byte[] vectorUniverse(String name) throws Exception {
        Matcher m = VECTOR.matcher(readSpec());
        while (m.find()) {
            if (m.group(1).equals(name)) {
                return hex(m.group(3));
            }
        }
        throw new IllegalStateException("vector " + name + " not found");
    }

    @Test
    public void everyVectorIsReproducedAndDecoded() throws Exception {
        Matcher m = VECTOR.matcher(readSpec());
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
        assertTrue("no vector read", count >= 7);
    }

    @Test
    public void spiderHelpersReproduceTheSpiderVector() throws Exception {
        byte[] universe = new byte[DmxFrame.UNIVERSE_SIZE];
        MindiSpider spider = new MindiSpider(1);
        spider.setWings(universe, 200, true);
        spider.setDimmer(universe, 255);
        spider.setLed(universe, 1, 255);
        spider.setLed(universe, 5, 255);

        assertEquals(2, spider.dmxChannel(MindiSpider.MOTOR_1)); // channel 1 is ignored by the Spider
        assertArrayEquals(vectorUniverse("mindi_spider_address1_code7"), universe);
    }

    @Test
    public void spot260xHelpersReproduceTheTwoHeadsVector() throws Exception {
        byte[] universe = new byte[DmxFrame.UNIVERSE_SIZE];

        ChauvetSpot260X head1 = new ChauvetSpot260X(17);
        head1.setPan(universe, 0x8000);
        head1.setTilt(universe, 0x4000);
        head1.setColor(universe, ChauvetSpot260X.Color.RED);
        head1.setGobo(universe, ChauvetSpot260X.Gobo.GOBO_3);
        head1.setGoboRotation(universe, ChauvetSpot260X.GoboRotation.CLOCKWISE, 128);
        head1.setPrism(universe, true);
        head1.setFocus(universe, 128);
        head1.lightOn(universe, 255);

        ChauvetSpot260X head2 = new ChauvetSpot260X(31);
        head2.setPan(universe, 0x8000);
        head2.setTilt(universe, 0x4000);
        head2.setColor(universe, ChauvetSpot260X.Color.BLUE);
        head2.setGobo(universe, ChauvetSpot260X.Gobo.OPEN);
        head2.setFocus(universe, 128);
        head2.setDimmer(universe, 255);
        head2.setStrobe(universe, 128, ChauvetSpot260X.StrobeEffect.NORMAL);

        assertArrayEquals(vectorUniverse("chauvet_spot260x_two_heads_code9"), universe);
    }

    @Test
    public void spot260xEightChannelModeHasNoDimmer() {
        ChauvetSpot260X spot = new ChauvetSpot260X(1, ChauvetSpot260X.Mode.CHANNELS_8);
        assertFalse(spot.has(ChauvetSpot260X.Function.DIMMER));
        assertEquals(8, spot.dmxChannel(ChauvetSpot260X.Function.SHUTTER));
    }

    @Test
    public void invalidFramesAreRejected() {
        assertFalse(DmxFrame.isFrame(new byte[DmxFrame.FRAME_LENGTH]));
    }
}
