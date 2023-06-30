using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using Godot;

namespace TraciConnector.Tudresden.Ws
{
    public class ShutdownHook
    {
        private bool shutdown;
        public ShutdownHook()
        {
            Setshutdown(false);
        }

        public virtual void Run()
        {
            //System.out_renamed.Println("Shutdown in progress...");
            Setshutdown(true);
            try
            {
                System.Threading.Thread.Sleep(3000);
            }
            catch (Exception ex)
            {
                GD.Print(ex.GetBaseException());
            }

            //System.out_renamed.Println("Shutdown finsihed");
        }

        public virtual void Setshutdown(bool shutdown)
        {
            this.shutdown = shutdown;
        }

        public virtual bool Isshutdown()
        {
            return shutdown;
        }
    }
}