class Witch extends Role{
	
	private String cloak;

	// constructor
	public Witch(){
		super();
		this.cloak = "";
	}
	public Witch(String name, String cloak){
		super(name, 280, 2000);
		this.cloak = cloak;
	}
	
	public void SmallFire(Role R){
		if(this.getMagic() >= 25){
			this.setMagic(this.getMagic() - 25);
			if(R instanceof Warrior){
				R.setLife(R.getLife() - 40);
			} else {
				R.setLife(R.getLife() - 60);
			}
			
			// is dead?
			if(R.getLife() <= 0){
				System.out.println(R.getName() + " is attaked by " + this.getName() + " and is dead.");
			}
		}
		else {
			System.out.println("The witch of " + this.getName() + "'s magic power is less than 25. So the attack is ineffective");
		}	
	}

	@Override
	public void print_char() {
		System.out.println(getName() + " with cloak: " + this.cloak + "> life: " + getLife() + ", magic: " + getMagic() + " " + (getLife()<= 0?"(Dead)":"")); 
	}

	@Override
	public void attack_method(Role R) {
		SmallFire(R);
	}
}