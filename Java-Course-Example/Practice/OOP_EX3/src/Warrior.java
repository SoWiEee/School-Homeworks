import java.security.SecureRandom;

public class Warrior extends Role{

    // constructor
    public Warrior() {}
    public Warrior(String Name, int Life, int Magic) {
        super(Name, Life, Magic);
    }

    public void NewMoon(Role R) {
        SecureRandom randomNumber = new SecureRandom();
        if(this.getMagic() > 10) {
            this.setMagic(this.getMagic() - 10);

            if(R instanceof Warrior)
                R.setLife(R.getLife() - 25);
            else if(R instanceof Mage)
                R.setLife(getLife() - 40);

            if(R.getLife() <= 0) {
                System.out.println(R.getName() + " was killed by " + this.getName() + '!');
                System.exit(0);
            }
            else if(R.getLife() < 40) {
                int rand= randomNumber.nextInt(100);
                if(rand < 10) R.DrinkDrug(new RedDrug("large"));
                else if(rand < 30) R.DrinkDrug(new RedDrug("middle"));
                else if(rand < 70) R.DrinkDrug(new RedDrug("small"));
            }

            if(this.getMagic() < 30) {
                int rand  = randomNumber.nextInt(100);
                if(rand < 10) this.DrinkDrug(new BlueDrug("large"));
                else if(rand < 30) this.DrinkDrug(new BlueDrug("middle"));
                else if(rand < 70) this.DrinkDrug(new BlueDrug("small"));
            }
        }
        else { System.out.println(this.getName() + " had no Magic Point..."); }
    }

    @Override
    public String toString() {
        return String.format("[*] %s: HP: %d, MP: %d", this.getName(), this.getLife(), this.getMagic());
    }

}