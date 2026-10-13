using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Windows.Devices.Bluetooth.Rfcomm;
using Windows.Networking;
using Windows.Networking.Sockets;
using Windows.Storage.Streams;

internal static class Program
{
    private static readonly Guid ServiceUuid = Guid.Parse("7b8d3f52-9f24-4c87-a4e1-3d11f5d8a701");
    private const int ApiPort = 8000;

    private static async Task Main()
    {
        Console.Title = "Hearlium Bluetooth Handshake";
        Console.WriteLine("Hearlium Parent PC Bluetooth Stage 2");
        Console.WriteLine("-------------------------------------");

        var serviceId = RfcommServiceId.FromUuid(ServiceUuid);
        var provider = await RfcommServiceProvider.CreateAsync(serviceId);
        var listener = new StreamSocketListener();

        listener.ConnectionReceived += async (_, args) =>
        {
            try
            {
                string payload = BuildHandshake();
                using var writer = new DataWriter(args.Socket.OutputStream)
{
    UnicodeEncoding = Windows.Storage.Streams.UnicodeEncoding.Utf8,
    ByteOrder = ByteOrder.LittleEndian
};
                };
                writer.WriteString(payload + "\n");
                await writer.StoreAsync();
                await writer.FlushAsync();
                Console.WriteLine($"Handshake sent: {payload}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Handshake error: {ex.Message}");
            }
            finally
            {
                args.Socket.Dispose();
            }
        };

        await listener.BindServiceNameAsync(
            serviceId.AsString(),
            SocketProtectionLevel.BluetoothEncryptionAllowNullAuthentication);

        provider.StartAdvertising(listener, true);

        Console.WriteLine($"Bluetooth RFCOMM service started.");
        Console.WriteLine($"UUID: {ServiceUuid}");
        Console.WriteLine($"API endpoint advertised: {GetLocalIPv4()}:{ApiPort}");
        Console.WriteLine("Keep this window open while pairing/connecting.");
        Console.WriteLine("Press Enter to stop.");
        Console.ReadLine();

        provider.StopAdvertising();
        listener.Dispose();
    }

    private static string BuildHandshake()
    {
        return JsonSerializer.Serialize(new
        {
            type = "hearlium_parent_pc",
            version = 1,
            host = GetLocalIPv4(),
            port = ApiPort,
            ready = true,
            transport = "wifi_lan"
        });
    }

    private static string GetLocalIPv4()
    {
        try
        {
            using var socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp);
            socket.Connect("8.8.8.8", 65530);
            if (socket.LocalEndPoint is IPEndPoint endpoint)
                return endpoint.Address.ToString();
        }
        catch { }

        foreach (var address in Dns.GetHostAddresses(Dns.GetHostName()))
        {
            if (address.AddressFamily == AddressFamily.InterNetwork &&
                !IPAddress.IsLoopback(address))
                return address.ToString();
        }

        return "127.0.0.1";
    }
}
