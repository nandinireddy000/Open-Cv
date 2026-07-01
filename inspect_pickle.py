import pickle

try:
    with open('source/CarParkPos.txt', 'rb') as f:
        posList = pickle.load(f)
        print("Successfully loaded pickle.")
        print(f"Type: {type(posList)}")
        print(f"Length: {len(posList)}")
        if len(posList) > 0:
            print(f"First item: {posList[0]}")
except Exception as e:
    print(f"Error loading pickle: {e}")
