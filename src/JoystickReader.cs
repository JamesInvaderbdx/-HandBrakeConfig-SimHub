using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace HandBrakeConfig
{
    public class JoystickInfo
    {
        public int    Id      { get; set; }
        public string Name    { get; set; }
        public int    NumAxes { get; set; }
        public int    NumBtns { get; set; }
    }

    public static class JoystickReader
    {
        [DllImport("winmm.dll")] static extern int joyGetNumDevs();
        [DllImport("winmm.dll")] static extern int joyGetDevCapsW(int id, ref JOYCAPSW caps, int size);
        [DllImport("winmm.dll")] static extern int joyGetPosEx  (int id, ref JOYINFOEX info);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        struct JOYCAPSW
        {
            public ushort wMid, wPid;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szPname;
            public uint wXmin, wXmax, wYmin, wYmax, wZmin, wZmax;
            public uint wNumButtons, wPeriodMin, wPeriodMax;
            public uint wRmin, wRmax, wUmin, wUmax, wVmin, wVmax;
            public uint wCaps, wMaxAxes, wNumAxes, wMaxButtons;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]  public string szRegKey;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szOEMVxD;
        }

        [StructLayout(LayoutKind.Sequential)]
        struct JOYINFOEX
        {
            public uint dwSize, dwFlags;
            public uint dwXpos, dwYpos, dwZpos;
            public uint dwRpos, dwUpos, dwVpos;
            public uint dwButtons, dwButtonNumber, dwPOV;
            public uint dwReserved1, dwReserved2;
        }

        public static List<JoystickInfo> EnumerateDevices()
        {
            var list = new List<JoystickInfo>();
            int max = joyGetNumDevs();
            for (int i = 0; i < max; i++)
            {
                var caps = new JOYCAPSW();
                if (joyGetDevCapsW(i, ref caps, Marshal.SizeOf(typeof(JOYCAPSW))) == 0)
                    list.Add(new JoystickInfo
                    {
                        Id      = i,
                        Name    = string.IsNullOrWhiteSpace(caps.szPname) ? "Joystick " + i : caps.szPname,
                        NumAxes = (int)caps.wNumAxes,
                        NumBtns = (int)caps.wNumButtons,
                    });
            }
            return list;
        }

        /// <summary>Retourne les 6 axes bruts [X,Y,Z,R,U,V], ou null si indisponible.</summary>
        public static uint[] ReadAxes(int deviceId)
        {
            var info = new JOYINFOEX();
            info.dwSize  = (uint)Marshal.SizeOf(typeof(JOYINFOEX));
            info.dwFlags = 0xFF;
            if (joyGetPosEx(deviceId, ref info) != 0) return null;
            return new uint[] { info.dwXpos, info.dwYpos, info.dwZpos,
                                info.dwRpos, info.dwUpos, info.dwVpos };
        }

        public static readonly string[] AxisNames = { "X", "Y", "Z", "R", "U", "V" };
    }
}
