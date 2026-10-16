using System;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

class DumpReaders
{
    static void Disasm(MethodDefinition m)
    {
        if (!m.HasBody) { Console.WriteLine("    (no body)"); return; }
        foreach (var ins in m.Body.Instructions)
            Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
    }

    static void Main(string[] args)
    {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        var mod = asm.MainModule;
        foreach (var t in mod.GetTypes())
        {
            // SurfaceFormat enum values
            if (t.Name == "SurfaceFormat" && t.IsEnum)
            {
                Console.WriteLine("=== enum SurfaceFormat ===");
                foreach (var f in t.Fields)
                    if (f.IsStatic && f.Constant != null)
                        Console.WriteLine("  {0} = {1}", f.Name, f.Constant);
            }
        }
        string[] want = args.Length > 1 ? args.Skip(1).ToArray() : new string[] {
            "SpriteFontReader", "Texture2DReader", "CharReader", "RectangleReader",
            "Vector3Reader", "StringReader", "ListReader`1", "ContentReader"
        };
        foreach (var t in mod.GetTypes())
        {
            if (Array.IndexOf(want, t.Name) < 0) continue;
            Console.WriteLine("=== TYPE {0} (base {1}) ===", t.FullName, t.BaseType);
            foreach (var m in t.Methods)
            {
                bool interesting = m.Name == "Read" || m.Name.StartsWith("ReadChar") ||
                    m.Name == "ReadString" || m.Name == "Read7BitEncodedInt" ||
                    m.Name == "ReadNullableChar" || m.Name == "ReadObject" ||
                    m.Name == "ReadAsset" || m.Name == "ReadSharedResource" ||
                    m.Name == "Write" || m.Name == "ReadValue" || m.Name == "Initialize";
                if (!interesting) continue;
                Console.WriteLine("  METHOD {0} static={1}", m.FullName, m.IsStatic);
                Disasm(m);
            }
        }
    }
}
