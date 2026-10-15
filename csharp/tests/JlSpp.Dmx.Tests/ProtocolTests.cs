// Tests contre spec/test_vectors.json (trames validees sur le materiel).

using System.Text.Json;
using JlSpp.Dmx;
using JlSpp.Dmx.Fixtures;

namespace JlSpp.Dmx.Tests;

public class ProtocolTests
{
    private sealed record Vector(string Name, int CodeNum, byte[] Universe, byte[] Frame);

    private static readonly JsonDocument Spec = JsonDocument.Parse(File.ReadAllText(FindSpec("test_vectors.json")));

    /// <summary>Remonte depuis le dossier de sortie jusqu'au dossier spec/ du depot.</summary>
    private static string FindSpec(string fileName)
    {
        for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir != null; dir = dir.Parent)
        {
            string candidate = Path.Combine(dir.FullName, "spec", fileName);
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }
        throw new FileNotFoundException($"spec/{fileName} introuvable au-dessus de {AppContext.BaseDirectory}");
    }

    private static IEnumerable<Vector> Vectors() =>
        Spec.RootElement.GetProperty("vectors").EnumerateArray().Select(v => new Vector(
            v.GetProperty("name").GetString()!,
            v.GetProperty("code_num").GetInt32(),
            Convert.FromHexString(v.GetProperty("universe_hex").GetString()!),
            Convert.FromHexString(v.GetProperty("frame_hex").GetString()!)));

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

    [Fact]
    public void Spider_helper_reproduces_the_spider_vector()
    {
        var universe = new byte[DmxFrame.UniverseSize];
        var spider = new MindiSpider(address: 1);
        spider.SetWings(universe, 200, mirror: true);
        spider.SetDimmer(universe, 255);
        spider.SetLed(universe, 1, 255);
        spider.SetLed(universe, 5, 255);

        Assert.Equal(2, spider.DmxChannel(SpiderChannel.Motor1)); // le canal 1 est ignore par le Spider
        Assert.Equal(Vectors().Single(v => v.Name == "mindi_spider_adresse1_code7").Universe, universe);
    }
}
