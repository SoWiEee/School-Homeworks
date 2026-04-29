abstract class Role{
	
	private String name;
	private int life;
	private int magic;

	// constructor
	public Role(){
		this.name = "";
		this.life = 0;
		this.magic = 0;
	}
	public Role(String name, int life, int magic){
		this.name = name;
		this.life = life;
		this.magic = magic;
	}

	public void setName(String name){
		this.name = name;
	}
	public void setLife(int life){
		this.life = life;
	}
	public void setMagic(int magic){
		this.magic = magic;
	}
	public String getName(){
		return name;
	}
	public int getLife(){
		return life;
	}
	public int getMagic(){
		return magic;
	}

	// 虛擬方法
	abstract public void print_char();
	abstract public void attack_method(Role R);
}