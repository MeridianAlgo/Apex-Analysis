import matplotlib.pyplot as plt
from src.utils import get_company_dir, save_plot

if __name__ == '__main__':
    ticker = 'TEST'
    # create a simple plot
    fig, ax = plt.subplots()
    ax.plot([1,2,3,4], [10, 20, 15, 30])
    ax.set_title('Test Plot')
    path = save_plot(fig, 'test_plot', ticker)
    print('Saved plot path:', path)
