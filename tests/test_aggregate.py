from src.aggregator import aggregate_analysis

if __name__ == '__main__':
    print('Running aggregate_analysis for TEST (no news)')
    result = aggregate_analysis('TEST', period='1d', num_articles=0)
    print('Result:')
    print(result)
    import os
    path = os.path.join('reports', 'TEST')
    print('\nFiles in', path)
    try:
        for f in sorted(os.listdir(path)):
            print(' -', f)
    except FileNotFoundError:
        print('No reports directory found')
