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

        public static void Open(string portName, int baud = 115200)
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
            try { Parse(_port.ReadLine()); } catch { }
        }

        static void Parse(string line)
        {
            line = line.Trim('\r', '\n', ' ');
            if (!uint.TryParse(line, out uint raw) || raw > 1023) return;
            lock (_lock) { _x = raw * 65535u / 1023u; _y = 0; }
        }

        // retourne [X, Y] mis a l'echelle 0-65535
        public static uint[] ReadAxes()
        {
            lock (_lock) return new[] { _x, _y };
        }
    }
}
