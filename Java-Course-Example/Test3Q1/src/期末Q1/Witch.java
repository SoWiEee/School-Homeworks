package 期末Q1;

public class Witch extends Role implements Jumpable{
	public Witch() {}
	public Witch(String name,int life,int magic,int level) {
		super(name,life,magic,level);
	}
private String clock = "clock";
public void SmallFire(Role R) {
	if(getMagic() >=25) {
		int damage;
		if(R instanceof Warrior) {
			damage = 40;
		}
		else {
			damage = 60;
		}
		System.out.printf("%s攻擊了%s\n",getName(),R.getName());
		setMagic(getMagic()-25);
		setLife(R.getLife()-damage);
	}
	else {
		System.out.printf("%s魔力不足\n", getName());
	}
	if(R.getLife()<=0) {
		System.out.printf("%s被%s打死了\n", R.getName(),getName());
	}
}
@Override
public void Drink(Drug D) {
	if(D instanceof RedDrug) {
		setLife(getLife()+((RedDrug)D).getAddLife());
	}
	else {
		setMagic(getMagic()+((BlueDrug)D).getAddMagic());
	}
}
@Override
public void print_char() {
	System.out.printf("名稱:%s,血量:%s,魔力:%s,等級:%s",getName(),getLife(),getMagic(),getLevel());
}
}
