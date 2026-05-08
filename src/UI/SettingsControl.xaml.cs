using System;
using System.Diagnostics;
using System.IO.Ports;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Navigation;
using System.Windows.Threading;

namespace HandBrakeConfig.UI
{
    public partial class SettingsControl : UserControl
    {
        readonly HandBrakeConfigPlugin _plugin;
        readonly DispatcherTimer        _timer;
        bool _loading = true;

        public SettingsControl(HandBrakeConfigPlugin plugin)
        {
            InitializeComponent();
            _plugin = plugin;

            _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(50) };
            _timer.Tick += Timer_Tick;
            _timer.Start();

            RefreshDeviceList();
            LoadFromSettings();
            _loading = false;
        }

        // ── Timer temps reel ─────────────────────────────────────────────────
        void Timer_Tick(object sender, EventArgs e)
        {
            uint? rawNullable = _plugin.GetRaw();

            if (_plugin.Settings.InputMode == InputMode.Serial)
                TbSerialStatus.Text = SerialReader.IsOpen ? "connected"
                    : string.IsNullOrEmpty(SerialReader.LastError) ? "no signal"
                    : "port busy";
            else
                TbAxisLive.Text = rawNullable.HasValue ? $"{rawNullable.Value} raw" : "---";

            if (rawNullable == null) return;
            uint raw = rawNullable.Value;

            uint span = _plugin.Settings.RawMax - _plugin.Settings.RawMin;
            double rawPct = span == 0 ? 0.0
                : Math.Max(0.0, Math.Min(1.0, (double)(raw - _plugin.Settings.RawMin) / span));
            double outVal = AxisProcessor.Process(raw, _plugin.Settings);

            PbRaw.Value = rawPct * 100;
            PbOut.Value = outVal * 100;
            TbRaw.Text  = $"{rawPct * 100:F0}%";
            TbOut.Text  = $"{outVal * 100:F0}%";

            // Couleur barre sortie
            PbOut.Foreground = outVal > 0.8
                ? System.Windows.Media.Brushes.Crimson
                : outVal > 0.4
                    ? System.Windows.Media.Brushes.Orange
                    : System.Windows.Media.Brushes.MediumSeaGreen;

            // Statut calibration
            if (_plugin.IsCalibrating)
                TbCalStatus.Text = $"  Cal en cours : {_plugin.CalMin} - {_plugin.CalMax}";
        }

        // ── Chargement UI depuis settings ─────────────────────────────────────
        void LoadFromSettings()
        {
            var s = _plugin.Settings;
            TbMin.Text      = s.RawMin.ToString();
            TbMax.Text      = s.RawMax.ToString();
            SlSmooth.Value  = s.SmoothN;
            TbSmoothVal.Text = s.SmoothN.ToString();
            SlDzLow.Value   = s.DeadzoneLow  * 100;
            SlDzHigh.Value  = s.DeadzoneHigh * 100;
            SlExpo.Value    = s.CurveExpo;
            TbExpo.Text     = s.CurveExpo.ToString("F1");

            switch (s.Curve)
            {
                case CurveType.Expo:   RbExpo.IsChecked   = true; break;
                case CurveType.SCurve: RbScurve.IsChecked = true; break;
                default:               RbLinear.IsChecked = true; break;
            }
            PanelExpo.Visibility = s.Curve == CurveType.Expo
                ? Visibility.Visible : Visibility.Collapsed;

            if (CbAxis.Items.Count > s.AxisIndex)
                CbAxis.SelectedIndex = s.AxisIndex;
            CbInvert.IsChecked = s.InvertAxis;
            CbVJoy.IsChecked = s.VJoyEnabled;
            if (s.VJoyEnabled) VJoyWriter.Acquire(s.VJoyDeviceId);

            // Mode
            if (s.InputMode == InputMode.Serial)
            {
                RbSerial.IsChecked  = true;
                PanelHID.Visibility    = Visibility.Collapsed;
                PanelSerial.Visibility = Visibility.Visible;
            }
            else
            {
                RbHID.IsChecked     = true;
                PanelHID.Visibility    = Visibility.Visible;
                PanelSerial.Visibility = Visibility.Collapsed;
            }

            // Serial
            RefreshSerialPorts();
            int portIdx = Array.IndexOf(SerialPort.GetPortNames(), s.SerialPort);
            if (portIdx >= 0) CbSerialPort.SelectedIndex = portIdx;
            if (s.SerialAxis == 1) RbSerialY.IsChecked = true;
            else                   RbSerialX.IsChecked = true;

            if (s.InputMode == InputMode.Serial && !string.IsNullOrEmpty(s.SerialPort))
                SerialReader.Open(s.SerialPort);
        }

        // ── Device ───────────────────────────────────────────────────────────
        void RefreshDeviceList()
        {
            CbDevice.Items.Clear();
            foreach (var d in JoystickReader.EnumerateDevices())
                CbDevice.Items.Add($"[{d.Id}] {d.Name}  ({d.NumAxes} axes)");

            if (_plugin.Settings.DeviceId < CbDevice.Items.Count)
                CbDevice.SelectedIndex = _plugin.Settings.DeviceId;
            else if (CbDevice.Items.Count > 0)
                CbDevice.SelectedIndex = 0;

            RefreshAxisList();
        }

        void RefreshAxisList()
        {
            CbAxis.Items.Clear();
            var axes = JoystickReader.ReadAxes(_plugin.Settings.DeviceId);
            for (int i = 0; i < JoystickReader.AxisNames.Length; i++)
            {
                uint val = axes != null && i < axes.Length ? axes[i] : 0;
                CbAxis.Items.Add($"{JoystickReader.AxisNames[i]}  ({val})");
            }
            int idx = _plugin.Settings.AxisIndex;
            CbAxis.SelectedIndex = idx < CbAxis.Items.Count ? idx : 0;
        }

        void BtnRefresh_Click(object s, RoutedEventArgs e) => RefreshDeviceList();

        // ── Mode ──────────────────────────────────────────────────────────────
        void InputMode_Changed(object s, RoutedEventArgs e)
        {
            if (_loading) return;
            bool serial = RbSerial.IsChecked == true;
            _plugin.Settings.InputMode = serial ? InputMode.Serial : InputMode.HID;
            PanelHID.Visibility    = serial ? Visibility.Collapsed : Visibility.Visible;
            PanelSerial.Visibility = serial ? Visibility.Visible   : Visibility.Collapsed;
            if (!serial) SerialReader.Close();
            else if (!string.IsNullOrEmpty(_plugin.Settings.SerialPort))
                SerialReader.Open(_plugin.Settings.SerialPort);
        }

        // ── Serial ────────────────────────────────────────────────────────────
        void RefreshSerialPorts()
        {
            CbSerialPort.Items.Clear();
            foreach (var p in SerialPort.GetPortNames())
                CbSerialPort.Items.Add(p);
        }

        void BtnSerialRefresh_Click(object s, RoutedEventArgs e) => RefreshSerialPorts();

        void CbSerialPort_SelectionChanged(object s, SelectionChangedEventArgs e)
        {
            if (_loading || CbSerialPort.SelectedItem == null) return;
            string port = CbSerialPort.SelectedItem.ToString();
            _plugin.Settings.SerialPort = port;
            SerialReader.Open(port);
        }

        void SerialAxis_Changed(object s, RoutedEventArgs e)
        {
            if (_loading) return;
            _plugin.Settings.SerialAxis = RbSerialY.IsChecked == true ? 1 : 0;
        }

        void CbDevice_SelectionChanged(object s, SelectionChangedEventArgs e)
        {
            if (_loading) return;
            _plugin.Settings.DeviceId = CbDevice.SelectedIndex;
            RefreshAxisList();
        }

        void CbAxis_SelectionChanged(object s, SelectionChangedEventArgs e)
        {
            if (_loading) return;
            _plugin.Settings.AxisIndex = CbAxis.SelectedIndex;
        }

        // ── Calibration ───────────────────────────────────────────────────────
        void CbVJoy_Changed(object s, RoutedEventArgs e)
        {
            if (_loading) return;
            bool enable = CbVJoy.IsChecked == true;
            _plugin.Settings.VJoyEnabled = enable;
            if (enable)
            {
                bool ok = VJoyWriter.Acquire(_plugin.Settings.VJoyDeviceId);
                TbVJoyStatus.Text = ok ? "connecté — Device 2 / Axe Y" : "erreur : " + VJoyWriter.LastError;
                TbVJoyStatus.Foreground = ok
                    ? System.Windows.Media.Brushes.MediumSeaGreen
                    : System.Windows.Media.Brushes.Crimson;
            }
            else
            {
                VJoyWriter.Release();
                TbVJoyStatus.Text = "";
            }
        }

        void CbInvert_Changed(object s, RoutedEventArgs e)
        {
            if (_loading) return;
            _plugin.Settings.InvertAxis = CbInvert.IsChecked == true;
        }

        void BtnApplyManual_Click(object s, RoutedEventArgs e)
        {
            if (uint.TryParse(TbMin.Text, out uint vmin) &&
                uint.TryParse(TbMax.Text, out uint vmax) && vmax > vmin)
            {
                _plugin.Settings.RawMin = vmin;
                _plugin.Settings.RawMax = vmax;
            }
        }

        void BtnCal_Click(object s, RoutedEventArgs e)
        {
            if (!_plugin.IsCalibrating)
            {
                _plugin.StartCalibration();
                BtnCal.Content    = "Arreter calibration";
                TbCalStatus.Text  = "  Tire et relache le frein a fond...";
                TbCalStatus.Foreground = System.Windows.Media.Brushes.Orange;
            }
            else
            {
                _plugin.StopCalibration();
                BtnCal.Content   = "Demarrer calibration auto";
                TbMin.Text       = _plugin.Settings.RawMin.ToString();
                TbMax.Text       = _plugin.Settings.RawMax.ToString();
                TbCalStatus.Text = $"  OK : {_plugin.Settings.RawMin} -> {_plugin.Settings.RawMax}";
                TbCalStatus.Foreground = System.Windows.Media.Brushes.MediumSeaGreen;
            }
        }

        // ── Deadzone ──────────────────────────────────────────────────────────
        void SlSmooth_Changed(object s, RoutedPropertyChangedEventArgs<double> e)
        {
            if (_loading) return;
            _plugin.Settings.SmoothN = (int)SlSmooth.Value;
            _plugin.ClearSmoothBuffer();
            TbSmoothVal.Text = _plugin.Settings.SmoothN.ToString();
        }

        void SlDzLow_Changed(object s, RoutedPropertyChangedEventArgs<double> e)
        {
            if (_loading) return;
            _plugin.Settings.DeadzoneLow = SlDzLow.Value / 100.0;
            TbDzLowVal.Text = $"{SlDzLow.Value:F1}%";
        }

        void SlDzHigh_Changed(object s, RoutedPropertyChangedEventArgs<double> e)
        {
            if (_loading) return;
            _plugin.Settings.DeadzoneHigh = SlDzHigh.Value / 100.0;
            TbDzHighVal.Text = $"{SlDzHigh.Value:F1}%";
        }

        // ── Courbe ────────────────────────────────────────────────────────────
        void Curve_Changed(object s, RoutedEventArgs e)
        {
            if (_loading) return;
            if (RbExpo.IsChecked   == true) _plugin.Settings.Curve = CurveType.Expo;
            else if (RbScurve.IsChecked == true) _plugin.Settings.Curve = CurveType.SCurve;
            else _plugin.Settings.Curve = CurveType.Linear;
            PanelExpo.Visibility = _plugin.Settings.Curve == CurveType.Expo
                ? Visibility.Visible : Visibility.Collapsed;
        }

        void SlExpo_Changed(object s, RoutedPropertyChangedEventArgs<double> e)
        {
            if (_loading) return;
            _plugin.Settings.CurveExpo = SlExpo.Value;
            TbExpo.Text = SlExpo.Value.ToString("F1");
        }

        // ── Save / Reset ──────────────────────────────────────────────────────
        void BtnSave_Click(object s, RoutedEventArgs e)
        {
            _plugin.End(_plugin.PluginManager);
            MessageBox.Show("Configuration sauvegardee !", "HandBrake Config",
                MessageBoxButton.OK, MessageBoxImage.Information);
        }

        void BtnReset_Click(object s, RoutedEventArgs e)
        {
            if (MessageBox.Show("Remettre les parametres par defaut ?", "HandBrake Config",
                MessageBoxButton.YesNo) == MessageBoxResult.Yes)
            {
                _plugin.Settings.InputMode    = InputMode.HID;
                _plugin.Settings.RawMin       = 0;
                _plugin.Settings.RawMax       = 65535;
                _plugin.Settings.DeadzoneLow  = 0.03;
                _plugin.Settings.DeadzoneHigh = 0.02;
                _plugin.Settings.Curve        = CurveType.Linear;
                _plugin.Settings.CurveExpo    = 2.0;
                _plugin.Settings.SmoothN      = 8;
                _loading = true;
                LoadFromSettings();
                _loading = false;
            }
        }

        void Hyperlink_Navigate(object s, RequestNavigateEventArgs e)
        {
            Process.Start(new ProcessStartInfo(e.Uri.AbsoluteUri) { UseShellExecute = true });
            e.Handled = true;
        }
    }
}
