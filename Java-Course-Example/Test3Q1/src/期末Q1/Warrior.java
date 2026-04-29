package 期末Q1;

public class Warrior extends Role implements Jumpable{
	public Warrior() {}
	public Warrior(String name,int life,int magic,int level) {
		super(name,life,magic,level);
	}
	private String Armor="Armor";
	public void NewMoon(Role R) {
		if(getMagic()>=10) {
			int damage;
			if(R instanceof Warrior) {
				damage = 25;
			}
			else {
				damage = 40;
			}
			System.out.printf("%s 攻擊了 %s\n",getName(),R.getName());
			setMagic(getMagic()-10);
			R.setLife(R.getLife()-damage);
		}
		else {
			System.out.printf("%s 魔力不足\n",getName());}
		if(R.getLife()<=0) {
			System.out.printf("%s 被%s打死了!!\n",R.getName(),getName());
		}
	}
	@Override
	public void Drink(Drug D) {
		if(D instanceof RedDrug) {
			setLife(getLife()+((RedDrug)D).getAddLife());}
		
	else {
		setMagic(getMagic()+((BlueDrug)D).getAddMagic());
	}}
	@Override
	public void print_char() {
		System.out.printf("名稱:%s,血量:%s,魔力:%s,等級:%s",getName(),getLife(),getMagic(),getLevel());
	}
}
