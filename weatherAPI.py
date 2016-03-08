import pyowm

owm = pyowm.OWM('d5210053d4c8c2dff1d59bc1fcf3368b')

# Will it be sunny tomorrow at this time in Milan (Italy) ?
forecast = owm.daily_forecast("Milan,it")
tomorrow = pyowm.timeutils.tomorrow()
forecast.will_be_sunny_at(tomorrow)  # Always True in Italy, right? ;-)

observation = owm.weather_at_place('Waterloo,ca')
w = observation.get_weather()
print(w)                      # <Weather - reference time=2013-12-18 09:20, 
                              # status=Clouds>

# Weather details
#print(w.get_wind())                  # {'speed': 4.6, 'deg': 330}
w.get_humidity()              # 87
print(w.get_temperature('celsius'))  # {'temp_max': 10.5, 'temp': 9.7, 'temp_min': 9.0}


# Search current weather observations in the surroundings of 
# lat=22.57W, lon=43.12S (Rio de Janeiro, BR)
observation_list = owm.weather_around_coords(-22.57, -43.12)
#print(observation_list)


# API Test
print('--------------begin test--------------')
print(owm.is_API_online())
data = owm.self_call_API("http://api.owm.io/air/1.0/uvi/current?lat=43.5&lon=-80.5")
print(data)

