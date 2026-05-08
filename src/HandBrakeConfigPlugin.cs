using System;
using System.Windows.Media;
using GameReaderCommon;
using SimHub.Plugins;

namespace HandBrakeConfig
{
    [PluginDescription("Calibration, zone morte et courbe de reponse pour frein a main USB")]
    [PluginName("HandBrake Config")]
    [PluginAuthor("eKLID")]
    public class HandBrakeConfigPlugin : IPlugin, IDataPlugin, IWPFSettings
    {
        public PluginManager PluginManager { get; set; }
        public HandBrakeSettings Settings  { get; private set; }

        private double _rawNormalized;
        private double _output;
        private readonly System.Collections.Generic.Queue<uint> _smoothBuf
            = new System.Collections.Generic.Queue<uint>();

        public bool   IsCalibrating   { get; private set; }
        public uint   CalMin          { get; private set; }
        public uint   CalMax          { get; private set; }
        public double SmoothedOutput  => _output;
        public double SmoothedRaw     => _rawNormalized;

        public void Init(PluginManager pluginManager)
        {
            Settings = this.ReadCommonSettings("HandBrakeSettings", () => new HandBrakeSettings());

            // Exposer les proprietes via delegates — pattern standard SimHub
            this.AttachDelegate("HandBrake.RawNormalized",  () => _rawNormalized);
            this.AttachDelegate("HandBrake.Output",          () => _output);
            this.AttachDelegate("HandBrake.OutputPercent",   () => Math.Round(_output * 100.0, 1));
            this.AttachDelegate("HandBrake.IsCalibrating",   () => IsCalibrating);
        }

        public uint? GetRaw()
        {
            if (Settings.InputMode == InputMode.Serial)
            {
                if (!SerialReader.IsOpen) return null;
                var sa = SerialReader.ReadAxes();
                return Settings.SerialAxis < sa.Length ? sa[Settings.SerialAxis] : (uint?)null;
            }
            var axes = JoystickReader.ReadAxes(Settings.DeviceId);
            if (axes == null || Settings.AxisIndex >= axes.Length) return null;
            return axes[Settings.AxisIndex];
        }

        private uint Smooth(uint raw)
        {
            int n = Math.Max(1, Settings.SmoothN);
            _smoothBuf.Enqueue(raw);
            while (_smoothBuf.Count > n) _smoothBuf.Dequeue();
            uint sum = 0;
            foreach (var v in _smoothBuf) sum += v;
            return (uint)(sum / _smoothBuf.Count);
        }

        public void ClearSmoothBuffer() => _smoothBuf.Clear();

        public void DataUpdate(PluginManager pluginManager, ref GameData data)
        {
            if (!Settings.Enabled) return;
            uint? raw = GetRaw();
            if (raw == null) return;
            uint r = Smooth(raw.Value);

            if (IsCalibrating)
            {
                if (r < CalMin) CalMin = r;
                if (r > CalMax) CalMax = r;
            }

            uint span = Settings.RawMax - Settings.RawMin;
            _rawNormalized = span == 0 ? 0.0
                : Math.Max(0.0, Math.Min(1.0, (double)(r - Settings.RawMin) / span));
            if (Settings.InvertAxis) _rawNormalized = 1.0 - _rawNormalized;

            _output = AxisProcessor.Process(r, Settings);

            if (Settings.VJoyEnabled)
                VJoyWriter.Write(_output, Settings.VJoyDeviceId, Settings.VJoyAxis);
        }

        public void End(PluginManager pluginManager)
        {
            VJoyWriter.Release();
            SerialReader.Close();
            this.SaveCommonSettings("HandBrakeSettings", Settings);
        }

        public void StartCalibration()
        {
            CalMin = 65535;
            CalMax = 0;
            IsCalibrating = true;
        }

        public void StopCalibration()
        {
            IsCalibrating = false;
            if (CalMax > CalMin)
            {
                Settings.RawMin = CalMin;
                Settings.RawMax = CalMax;
            }
        }

        public System.Windows.Controls.Control GetWPFSettingsControl(PluginManager pluginManager)
            => new UI.SettingsControl(this);

        public ImageSource PictureIcon
        {
            get
            {
                try
                {
                    var uri = new Uri("pack://application:,,,/HandBrakeConfig;component/icon_32.png");
                    return new System.Windows.Media.Imaging.BitmapImage(uri);
                }
                catch { return null; }
            }
        }
        public string LeftMenuTitle => "HandBrake Config";
    }
}
