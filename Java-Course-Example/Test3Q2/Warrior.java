public class Warrior extends Role{
    private String armor;

    // constructor
    public Warrior(){
        super();
        this.armor = "";
    }
    public Warrior(String name, int life, int magic ,String armor){
        super(name, life, magic);
        this.armor = armor;
    }

    public String getArmor(){ return armor; }

    // skill
    public void NewMoon(Role R){
        if(this.getMagic() >= 10){
            if(R instanceof Warrior){
                R.setLife(R.getLife() - 25);
            }
            if(R instanceof Witch){
                R.setLife(R.getLife() - 40);
            }
            this.setMagic(this.getMagic() - 10);
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
        return String.format("[Dead] %s: HP: %d, MP: %d, Armor: %s", this.getName(), this.getLife(), this.getMagic(), this.getArmor());
    }
}
