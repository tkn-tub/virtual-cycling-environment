using System;
using System.Security.Cryptography;
using System.Text;

public class MD5Hasher
{
	public static string getMD5(string in_str)
	{
		return getMD5Uint(in_str).ToString();
	}

	// siehe https://dotnet-snippets.de/snippet/gibt-den-md5-hash-eines-stings-als-string-zurueck/18
	public static uint getMD5Uint(string in_str)
	{
		if (in_str == null || in_str.Length == 0)
		{
			return 0;
		}

		MD5 md5 = new MD5CryptoServiceProvider();
		byte[] tth = Encoding.Default.GetBytes(in_str);
		byte[] hash = md5.ComputeHash(tth);
		byte[] out_byte = new Byte[] { hash[3], hash[2], hash[1], hash[0] };

		return System.BitConverter.ToUInt32(out_byte, 0);
	}
}
