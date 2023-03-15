# Test task at UNIKA

## Examples:

0. Crete virtual environment.
   ```console
   python3.11 -m venv ./venv
   source venv/bin/activate
   ```
1. TCP Server in worker mode.
   
   ```console
   python main.py
   python test.py
   ```
2. TCP Server in cluster mode.

   ```console
   python main.py -c
   python test.py
   python test.py -q
   ```
3. TCP Server in cluster mode without process recovery.

   ```console
   python main.py -c -r
   python test.py
   python test.py -q
   ```
4. TCP Server in cluster mode without reuse port option.

   ```console
   python main.py -c --reuse-port
   python test.py
   python test.py -q
   ```