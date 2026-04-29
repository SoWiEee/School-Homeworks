public class Priest extends Role {

    // constructor
    public Priest() {}
    public Priest(String Name, int Life, int Magic) {
        super(Name, Life, Magic);
    }

    public void Dark(Role R) {
        if(this.getMagic() > 20) {
            this.setMagic(this.getMagic() - 20);

            if(R instanceof Warrior)
                R.setLife(R.getLife() - 30);
            else if(R instanceof Mage)
                R.setLife(getLife() - 50);
            else if(R instanceof Priest)
                R.setLife(getLife() - 40);

            if(R.getLife() <= 0) {
                System.out.println(R.getName() + " was killed by " + this.getName() + '!');
                System.exit(0);
            }
        }
        else { System.out.println(this.getName() + " had no Magic Point..."); }
    }

    @Override
    public String toString() {
        return String.format("[*] %s: HP: %d, MP: %d", this.getName(), this.getLife(), this.getMagic());
    }
}