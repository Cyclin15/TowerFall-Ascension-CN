using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class FinalCheck {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        Console.WriteLine("assembly OK: " + asm.Name);
        int cn = 0, total = 0;
        var found = new System.Collections.Generic.List<string>();
        foreach (var t in asm.MainModule.GetTypes())
        foreach (var m in t.Methods) {
            if (!m.HasBody) continue;
            foreach (var ins in m.Body.Instructions)
                if (ins.OpCode == OpCodes.Ldstr) {
                    total++;
                    string s = (string)ins.Operand;
                    if (s.IndexOf('\u4e00') >= 0 || s.IndexOf('\u51fb') >= 0) {
                        foreach (char c in s)
                            if (c >= 0x4e00 && c <= 0x9fff) { cn++; break; }
                        if (found.Count < 5) found.Add(t.Name + "::" + m.Name + ": " + s);
                    }
                }
        }
        Console.WriteLine("ldstr total: " + total + ", with CJK: " + cn);
        foreach (var f in found) Console.WriteLine("  " + f);
    }
}
