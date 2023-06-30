using System;

public interface IThreadedNetWorker
{
	bool SaveNextFrame(Asmp.Message msg);
	bool HasResults();
	Asmp.Message Recv();
	void Destroy();
}
