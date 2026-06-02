import re


def parse_time(file):
    """ Parse profile timing outputs

    ```
        import matplotlib.pyplot as plt

        # Parse data
        cumulative_times, self_times = parse_time('path/to/time.000000')

        # Extract times of relevant routines
        routines = ['ISDF_SERIAL_ACE_W_UNPACKED', 'POISSON_SOLVE', 'CONSTRUCT_DENSITY_MATRIX_PACKED']
        time_per_call = [cumulative_times[name]['TIME_PER_CALL'] for name in routines]
        total_time = [cumulative_times[name]['TOTAL_TIME'] for name in routines]

        # Plot
        plt.figure(figsize=(12, 6))
        plt.bar(routines, total_time)
        plt.xlabel('Routine')
        plt.ylabel('Total Time (s)')
        plt.title('Total Time per Routine')
        plt.xticks(rotation=45, ha='right')
        plt.show()
    ```
    :param file:
    :return:
    """
    with open(file, mode='r') as fid:
        lines = fid.readlines()

    nheader = 4
    cumulative_times = {}
    self_times = {}
    # corrupt_lines = []
    stars = re.compile(r'\*+')  # any contiguous block of '*'

    for line in lines[nheader:]:

        # If the line contains stars, this means MFLOPS has probably been exceeded
        # max formatting value.
        # Remove any stars and replace with -10
        line = stars.sub('-10', line)

        entry = line.split()
        name = entry[0]

        # If there are not the correct number of line breaks, that means
        # one number was large enough to crash into the preceding line,
        # but not so large it turned to stars (still an issue with MFLOPS).
        if len(entry) < 14:
            # Extract the viable data from cumulative time and zero the rest
            cumulative_times[name] = {'NUM_CALLS': int(entry[1]),
                                      'TOTAL_TIME': float(entry[2]),
                                      'TIME_PER_CALL': float(entry[3])
                                      }
        else:
            cumulative_times[name] = {'NUM_CALLS': int(entry[1]),
                                      'TOTAL_TIME': float(entry[2]),
                                      'TIME_PER_CALL': float(entry[3]),
                                      'MIN_TIME': float(entry[4]),
                                      'MFLOPS': float(entry[5]),
                                      'MBYTES/S': float(entry[6]),
                                      'TIME(%)': float(entry[7])
                                      }
            self_times[name] = {'TOTAL_TIME': float(entry[9]),
                                'TIME_PER_CALL': float(entry[10]),
                                'MFLOPS': float(entry[11]),
                                'MBYTES/S': float(entry[12]),
                                'TIME(%)': float(entry[13])
                            }

    return cumulative_times, self_times
