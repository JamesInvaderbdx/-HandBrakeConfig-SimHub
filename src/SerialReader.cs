using System.IO.Ports;

namespace HandBrakeConfig
{
    public static class SerialReader
    {
        static SerialPort _port;
        static uint _x, _y;
        static readonly object _lock = new object();

        public static bool IsOpen => _port != null && _port.IsOpen;
        public static string LastError { get; private set; } = "";

        public static void Open(string portName, int baud = 9600)
        {
            Close();
            LastError = "";
            _port = new SerialPort(portName, baud) { ReadTimeout = 100 };
            _port.DataReceived += OnData;
            try { _port.Open(); }
            catch (System.Exception ex) { LastError = ex.Message; _port = null; }
        }

        public static void Close()
        {
            if (_port == null) return;
            _port.DataReceived -= OnData;
            if (_port.IsOpen) try { _port.Close(); } catch { }
            _port = null;
        }

        static void OnData(object s, SerialDataReceivedEventArgs e)
        {
            try { Parse(_port.ReadLine().Trim()); } catch { }
        }

        static void Parse(string line)
        {
            int xi = line.IndexOf("X:"), yi = line.IndexOf(" Y:");
            if (xi < 0 || yi < 0) return;
            int xEnd = line.IndexOf(' ', xi);
            int yEnd = line.IndexOf(' ', yi + 1);
            string xs = line.Substring(xi + 2, (xEnd < 0 ? line.Length : xEnd) - xi - 2);
            string ys = line.Substring(yi + 3, (yEnd < 0 ? line.Length : yEnd) - yi - 3);
            if (uint.TryParse(xs, out uint xv) && uint.TryParse(ys, out uint yv))
                lock (_lock) { _x = xv * 65535u / 1023u; _y = yv * 65535u / 1023u; }
        }

        // retourne [X, Y] mis a l'echelle 0-65535
        public static uint[] ReadAxes()
        {
            lock (_lock) return new[] { _x, _y };
        }
    }
}
