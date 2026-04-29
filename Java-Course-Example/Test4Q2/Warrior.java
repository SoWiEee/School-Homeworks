class Warrior extends Role {

	private String armor;

	// constructor
	public Warrior(){
		super();
		this.armor = "";
	}
	public Warrior(String name, String armor){
		super(name, 400, 1000);
		this.armor = armor;
	}
	
	public void NewMoon(Role R){
		if(this.getMagic() >= 10){
			this.setMagic(this.getMagic() - 10);
			if(R instanceof Warrior){
				R.setLife(R.getLife() - 25);
			} else {
				R.setLife(R.getLife() - 40);
			}
			
			// is dead?
			if(R.getLife() <= 0){
				System.out.println(R.getName() + " is attaked by " + this.getName() + " and is dead.");
			}
		}
		else {
			System.out.println("[X] The Warroir of " + this.getName() + "'s MP < 10 !");
		}	
	}

	@Override
	public void print_char() {
		System.out.println(getName() + " with armor: " + this.armor + "> life: " + getLife() + ", magic: " + getMagic() + " " + (getLife()<0?"dead":"")); 
	}

	@Override
	public void attack_method(Role R) {
		NewMoon(R);
	}
}