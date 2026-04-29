package ´Á¥½Q1;

 interface Jumpable {
	public static double JUMPUNIT = 12.25;
	public static double Jump(int level) {
		return JUMPUNIT*level*level;
	 }
}