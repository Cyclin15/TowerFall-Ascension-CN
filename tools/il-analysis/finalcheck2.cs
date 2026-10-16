using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class FinalCheck2 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        int cn = 0, total = 0;
        foreach (var t in asm.MainModule.GetTypes())
        foreach (var m in t.Methods) {
            if (!m.HasBody) continue;
            foreach (var ins in m.Body.Instructions)
                if (ins.OpCode == OpCodes.Ldstr) {
                    total++;
                    string s = (string)ins.Operand;
                    foreach (char c in s)
                        if (c >= 0x4e00 && c <= 0x9fff) { cn++; break; }
                }
        }
        Console.WriteLine("ldstr total: " + total + ", CJK: " + cn);
    }
}
