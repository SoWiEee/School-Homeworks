
public class main2 {

	public static void main(String[] args) {
		student2[] students;
		int lowest[]= new int[3];
		int highest []=new int[3];
		int aver_count [] = new int [11];
		
		students =new student2[20];
		lowest[0] = 100;
		highest[0] = 0;
		
		for (int i = 0; i<11;i++)
		{
			aver_count[i] = 0;
		}
		
		
		for(int i = 1;i<20;i++)
		{
			students[i-1] = new student2();
			for(int j = 0;j<3;j++)
			{
				if(students[i-1].get_test(j)<lowest[0])
				{
					lowest[0]=students[i-1].get_test(j);
					lowest[1]=j+1;
					lowest[2]=i;
				}
				if(students[i-1].get_test(j)>highest[0])
				{
					highest[0]=students[i-1].get_test(j);
					highest[1]=j+1;
					highest[2]=i;
				}
			}
			int a = (int) students[i-1].get_aver()/10%10;
			aver_count[a] = aver_count[a]+1;
			System.out.printf("Student %d\\t%d\\t%d\\t%d\\t%.2f\\n",i,students[i-1].get_test(0),students[i-1].get_test(1),students[i-1].get_test(2),students[i-1].get_aver());
		}
		
		System.out.println();
		System.out.println("Lowest grade in the grade book is "+lowest[0]+" which is Test "+lowest[1]+" of Student "+lowest[2]);
		System.out.println("Highest grade in the grade book is "+highest[0]+" which is Test "+highest[1]+" of Student "+highest[2]);
		
		
	}

}
