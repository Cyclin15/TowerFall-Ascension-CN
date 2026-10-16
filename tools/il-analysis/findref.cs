using System;
using Mono.Cecil;
using Mono.Cecil.Cil;

class FindRef
{
    static void Main(string[] args)
    {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        string memberName = args[1];
        foreach (var module in asm.Modules)
        foreach (var type in module.GetTypes())
        foreach (var method in type.Methods)
        {
            if (!method.HasBody) continue;
            foreach (var ins in method.Body.Instructions)
            {
                MethodReference mr = ins.Operand as MethodReference;
                if (mr != null && mr.Name == memberName)
                    Console.WriteLine(type.FullName + "::" + method.Name + " -> " + mr.FullName);
                FieldReference fr = ins.Operand as FieldReference;
                if (fr != null && fr.Name == memberName)
                    Console.WriteLine(type.FullName + "::" + method.Name + " -> [field] " + fr.FullName);
            }
        }
    }
}
