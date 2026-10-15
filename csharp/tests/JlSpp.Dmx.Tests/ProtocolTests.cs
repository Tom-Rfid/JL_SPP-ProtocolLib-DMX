// Tests against spec/test_vectors.json (frames validated on the hardware) and the
// fixture charts in spec/fixtures/.

using System.Text.Json;
using JlSpp.Dmx;
using JlSpp.Dmx.Fixtures;

namespace JlSpp.Dmx.Tests;

public class ProtocolTests
{
    private sealed record Vector(string Name, int CodeNum, byte[] Universe, byte[] Frame);

    private static readonly JsonDocument Spec = JsonDocument.Parse(File.ReadAllText(FindSpec("test_vectors.json")));

    /// <summary>Walks up from the output folder to the spec/ folder of the repository.</summary>
    internal static string FindSpec(string relativePath)
    {
        for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir != null; dir = dir.Parent)
        {
            string candidate = Path.Combine(dir.FullName, "spec", relativePath);
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }
        throw new FileNotFoundException($"spec/{relativePath} not found above {AppContext.BaseDirectory}");
    }

    private static IEnumerable<Vector> Vectors() =>
        Spec.RootElement.GetProperty("vectors").EnumerateArray().Select(v => new Vector(
            v.GetProperty("name").GetString()!,
            v.GetProperty("code_num").GetInt32(),
            Convert.FromHexString(v.GetProperty("universe_hex").GetString()!),
            Convert.FromHexString(v.GetProperty("frame_hex").GetString()!)));

    internal static byte[] VectorUniverse(string name) => Vectors().Single(v => v.Name == name).Universe;

    public static IEnumerable<object[]> VectorNames() => Vectors().Select(v => new object[] { v.Name });

    [Theory]
    [MemberData(nameof(VectorNames))]
    public void Build_matches_the_vector_byte_for_byte(string name)
    {
        var v = Vectors().Single(x => x.Name == name);
        Assert.Equal(Convert.ToHexStringLower(v.Frame), Convert.ToHexStringLower(DmxFrame.Build(v.Universe, (byte)v.CodeNum)));
    }

    [Theory]
    [MemberData(nameof(VectorNames))]
    public void Decode_gives_back_the_universe(string name)
    {
        var v = Vectors().Single(x => x.Name == name);
        Assert.Equal(v.Universe, DmxFrame.DecodeUniverse(v.Frame, out byte code));
        Assert.Equal(v.CodeNum, code);
    }

    [Fact]
    public void Handshakes_match_the_spec()
    {
        Assert.Equal(Spec.RootElement.GetProperty("handshake_connect_hex").GetString(),
            Convert.ToHexStringLower(DmxFrame.HandshakeConnect()));
        Assert.Equal(Spec.RootElement.GetProperty("handshake_disconnect_hex").GetString(),
            Convert.ToHexStringLower(DmxFrame.HandshakeDisconnect()));
    }

    [Fact]
    public void Invalid_frames_are_rejected()
    {
        Assert.False(DmxFrame.IsFrame(new byte[521]));
        Assert.Throws<ArgumentException>(() => DmxFrame.Build(new byte[10], 1));
    }
}

public class MindiSpiderTests
{
    [Fact]
    public void Helpers_reproduce_the_spider_vector()
    {
        var universe = new byte[DmxFrame.UniverseSize];
        var spider = new MindiSpider(address: 1);
        spider.SetWings(universe, 200, mirror: true);
        spider.SetDimmer(universe, 255);
        spider.SetLed(universe, 1, 255);
        spider.SetLed(universe, 5, 255);

        Assert.Equal(2, spider.DmxChannel(SpiderChannel.Motor1)); // channel 1 is ignored by the Spider
        Assert.Equal(ProtocolTests.VectorUniverse("mindi_spider_address1_code7"), universe);
    }
}

public class ChauvetSpot260XTests
{
    private static readonly JsonDocument Chart =
        JsonDocument.Parse(File.ReadAllText(ProtocolTests.FindSpec(Path.Combine("fixtures", "chauvet-intimidator-spot-260x.json"))));

    [Fact]
    public void Helpers_reproduce_the_two_heads_vector()
    {
        var universe = new byte[DmxFrame.UniverseSize];

        var head1 = new ChauvetSpot260X(address: 17);
        head1.SetPan(universe, 0x8000);
        head1.SetTilt(universe, 0x4000);
        head1.SetColor(universe, Spot260XColor.Red);
        head1.SetGobo(universe, Spot260XGobo.Gobo3);
        head1.SetGoboRotation(universe, GoboRotation.Clockwise, speed: 128);
        head1.SetPrism(universe, true);
        head1.SetFocus(universe, 128);
        head1.LightOn(universe);

        var head2 = new ChauvetSpot260X(address: 31);
        head2.SetPan(universe, 0x8000);
        head2.SetTilt(universe, 0x4000);
        head2.SetColor(universe, Spot260XColor.Blue);
        head2.SetGobo(universe, Spot260XGobo.Open);
        head2.SetFocus(universe, 128);
        head2.SetDimmer(universe, 255);
        head2.SetStrobe(universe, speed: 128);

        Assert.Equal(ProtocolTests.VectorUniverse("chauvet_spot260x_two_heads_code9"), universe);
    }

    [Fact]
    public void Channel_numbers_match_the_chart()
    {
        var spot14 = new ChauvetSpot260X(1, Spot260XMode.Channels14);
        var spot8 = new ChauvetSpot260X(1, Spot260XMode.Channels8);

        foreach (var channel in Chart.RootElement.GetProperty("channels").EnumerateArray())
        {
            // "color_wheel" -> ColorWheel
            string name = string.Concat(channel.GetProperty("function").GetString()!.Split('_')
                .Select(part => char.ToUpperInvariant(part[0]) + part[1..]));
            var function = Enum.Parse<Spot260XFunction>(name);

            Assert.Equal(channel.GetProperty("channel_14ch").GetInt32(), spot14.DmxChannel(function));
            var ch8 = channel.GetProperty("channel_8ch");
            if (ch8.ValueKind == JsonValueKind.Null)
            {
                Assert.False(spot8.Has(function));
            }
            else
            {
                Assert.Equal(ch8.GetInt32(), spot8.DmxChannel(function));
            }
        }
    }

    [Fact]
    public void Eight_channel_mode_has_no_dimmer_and_no_fine_pan()
    {
        var universe = new byte[DmxFrame.UniverseSize];
        var spot = new ChauvetSpot260X(1, Spot260XMode.Channels8);

        Assert.Throws<InvalidOperationException>(() => spot.SetDimmer(universe, 255));
        spot.SetPan(universe, 0x1234);
        Assert.Equal(0x12, universe[0]);
        Assert.Equal(0, universe[1]);
    }

    [Fact]
    public void Speeds_reach_the_ends_of_the_ranges()
    {
        var universe = new byte[DmxFrame.UniverseSize];
        var spot = new ChauvetSpot260X(1);

        spot.SetStrobe(universe, 255, StrobeEffect.Random);
        Assert.Equal(215, universe[spot.DmxChannel(Spot260XFunction.Shutter) - 1]);
        spot.SetColorRainbow(universe, 255);
        Assert.Equal(190, universe[spot.DmxChannel(Spot260XFunction.ColorWheel) - 1]);
        spot.SetMovementMacro(universe, 8, soundActive: true);
        Assert.Equal(251, universe[spot.DmxChannel(Spot260XFunction.MovementMacro) - 1]);
    }

    [Fact]
    public void Address_must_leave_room_for_the_channels()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new ChauvetSpot260X(500));
        _ = new ChauvetSpot260X(505, Spot260XMode.Channels8);
    }
}
