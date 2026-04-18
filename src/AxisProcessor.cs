using System;

namespace HandBrakeConfig
{
    public static class AxisProcessor
    {
        public static double Process(uint raw, HandBrakeSettings s)
        {
            double val = Calibrate(raw, s.RawMin, s.RawMax);
            if (s.InvertAxis) val = 1.0 - val;
            val = Deadzone(val, s.DeadzoneLow, s.DeadzoneHigh);
            val = Curve(val, s.Curve, s.CurveExpo);
            return val;
        }

        static double Calibrate(uint raw, uint min, uint max)
        {
            if (max == min) return 0.0;
            double v = ((double)raw - min) / (max - min);
            return Math.Max(0.0, Math.Min(1.0, v));
        }

        static double Deadzone(double v, double low, double high)
        {
            if (v <= low)        return 0.0;
            if (v >= 1.0 - high) return 1.0;
            double active = 1.0 - low - high;
            return (v - low) / active;
        }

        static double Curve(double v, CurveType curve, double expo)
        {
            switch (curve)
            {
                case CurveType.Expo:   return Math.Pow(v, expo);
                case CurveType.SCurve: return v * v * (3 - 2 * v);
                default:               return v;
            }
        }
    }
}
