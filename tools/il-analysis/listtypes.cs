using System;
using Mono.Cecil;
class ListTypes {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        string pat = args[1].ToLower();
        foreach (var t in asm.MainModule.GetTypes())
            if (t.FullName.ToLower().Contains(pat))
                Console.WriteLine(t.FullName);
    }
}
