namespace HandBrakeConfig
{
    public enum CurveType { Linear, Expo, SCurve }
    public enum InputMode { HID, Serial }

    public class HandBrakeSettings
    {
        public InputMode InputMode      { get; set; } = InputMode.HID;
        public int       DeviceId      { get; set; } = 0;
        public int       AxisIndex     { get; set; } = 3;
        public string    SerialPort    { get; set; } = "COM4";
        public int       SerialAxis    { get; set; } = 0;   // 0=X 1=Y
        public uint      RawMin        { get; set; } = 0;
        public uint      RawMax        { get; set; } = 65535;
        public double    DeadzoneLow   { get; set; } = 0.03;
        public double    DeadzoneHigh  { get; set; } = 0.02;
        public CurveType Curve         { get; set; } = CurveType.Linear;
        public double    CurveExpo     { get; set; } = 2.0;
        public bool      InvertAxis    { get; set; } = false;
        public bool      VJoyEnabled   { get; set; } = false;
        public uint      VJoyDeviceId  { get; set; } = 2;
        public uint      VJoyAxis      { get; set; } = 0x31; // Y par defaut
        public bool      Enabled       { get; set; } = true;
    }
}
