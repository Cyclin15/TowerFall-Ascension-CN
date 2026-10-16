using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Content;

class DeviceService : IGraphicsDeviceService
{
    public GraphicsDevice GraphicsDevice { get; private set; }
    public event EventHandler<EventArgs> DeviceCreated;
    public event EventHandler<EventArgs> DeviceDisposing;
    public event EventHandler<EventArgs> DeviceReset;
    public event EventHandler<EventArgs> DeviceResetting;
    public DeviceService(GraphicsDevice d) { GraphicsDevice = d; }
}

class Provider : IServiceProvider
{
    DeviceService svc;
    public Provider(GraphicsDevice d) { svc = new DeviceService(d); }
    public object GetService(Type t) { return t == typeof(IGraphicsDeviceService) ? svc : null; }
}

class FontTest
{
    [STAThread]
    static int Main(string[] args)
    {
        var form = new System.Windows.Forms.Form();
        form.Show(); form.Hide();
        var pp = new PresentationParameters();
        pp.BackBufferWidth = 32; pp.BackBufferHeight = 32;
        pp.DeviceWindowHandle = form.Handle;
        pp.IsFullScreen = false;
        GraphicsDevice dev;
        try
        {
            dev = new GraphicsDevice(GraphicsAdapter.DefaultAdapter, GraphicsProfile.Reach, pp);
        }
        catch (Exception e)
        {
            Console.WriteLine("device fail: " + e.Message);
            return 2;
        }
        var cm = new ContentManager(new Provider(dev), args[1]);
        try
        {
            var font = cm.Load<SpriteFont>(args[0]);
            Console.WriteLine("loaded OK");
            Console.WriteLine("LineSpacing=" + font.LineSpacing);
            Console.WriteLine("DefaultCharacter=" + (font.DefaultCharacter.HasValue ? "'" + font.DefaultCharacter.Value + "'" : "null"));
            var chars = new List<char>(font.Characters);
            Console.WriteLine("Characters count=" + chars.Count);
            chars.Sort();
            Console.WriteLine("first: " + (int)chars[0] + " last: " + (int)chars[chars.Count - 1]);
            // find CJK range presence
            int cjk = 0; foreach (char c in chars) if (c >= 0x4e00 && c <= 0x9fff) cjk++;
            Console.WriteLine("CJK chars in font: " + cjk);
            string probe = "本游戏自动存档！";
            foreach (char c in probe)
                Console.WriteLine("  '" + c + "' (U+" + ((int)c).ToString("X4") + ") present: " + (chars.BinarySearch(c) >= 0));
            var m = font.MeasureString(probe);
            Console.WriteLine("MeasureString('" + probe + "') = " + m.X + " x " + m.Y);
            var m2 = font.MeasureString("ARCHER SELECT");
            Console.WriteLine("MeasureString('ARCHER SELECT') = " + m2.X + " x " + m2.Y);
            // dump first 40 chars as codes
            var sb = new System.Text.StringBuilder();
            foreach (char c in chars) { sb.Append(((int)c).ToString("X4")); sb.Append(' '); }
            Console.WriteLine("all chars: " + sb.ToString());
            return 0;
        }
        catch (Exception e)
        {
            Console.WriteLine("LOAD FAIL: " + e.GetType().Name + ": " + e.Message);
            Console.WriteLine(e.StackTrace);
            return 1;
        }
    }
}
