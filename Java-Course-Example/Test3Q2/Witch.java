public class Witch extends Role{
    private String cloak;

    // constructor
    public Witch(){
        super();
        this.cloak = "";
    }
    public Witch(String name, int life, int magic, String cloak){
        super(name, life, magic);
        this.cloak = cloak;
    }

    public String getCloak(){ return cloak; }

    // skill
    public void SmallFire(Role R){
        if(this.getMagic() >= 25){
            if(R instanceof Warrior){
                R.setLife(R.getLife() - 40);
            }
            if(R instanceof Witch){
                R.setLife(R.getLife() - 60);
            }
            this.setMagic(this.getMagic() - 25);
            if(R.getLife() < 0){ R.setLife(0); }
        }
    }

    @Override
    public void Drink(Drug D){
        if(D instanceof RedDrug){
            setLife(((RedDrug) D).getAddLife());
        }else{
            setLife(((BlueDrug) D).getAddMagic());
        }
    }

    @Override
    public void print_char(){
        System.out.println(this);
    }

    @Override
    public String toString() {
        return String.format("[Dead] %s: HP: %d, MP: %d, Cloak: %s", this.getName(), this.getLife(), this.getMagic(), this.getCloak());
    }
}
