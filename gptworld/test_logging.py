import subprocess
import multiprocessing
import os
import time
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_backend():
    subprocess.run(['python app.py'], cwd=f'{CURRENT_DIR}/../game/text_grid', capture_output=True, shell=True)

def run_frontend():
    subprocess.run(['npm run --silent dev'], cwd=f'{CURRENT_DIR}/../game/text_grid/frontend', capture_output=True, shell=True)
   
    # print( 'exit status:', p1.returncode )
    # print( 'stdout:', p1.stdout.decode() )
    # print( 'stderr:', p1.stderr.decode() )
    # print( 'exit status:', p2.returncode )
    # print( 'stdout:', p2.stdout.decode() )
    # print( 'stderr:', p2.stderr.decode() )


if __name__ == "__main__":

    import multiprocessing

    
    process_backend = multiprocessing.Process(target=run_backend)
    process_frontend = multiprocessing.Process(target=run_frontend)
    process_backend.start()
    process_frontend.start()

    while True:
        print(1)
        time.sleep(1)
