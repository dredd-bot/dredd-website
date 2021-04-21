from datetime import datetime

class WebsiteTheme:
    icon = 'normal.png'
    color = '#2E4C8C'
    if datetime.utcnow().month == 2 and datetime.utcnow().day <= 15:
        icon = 'valentine.png'
        color = '#F2778D'
    elif datetime.utcnow().month == 4 and datetime.utcnow().day <= 15:
        icon = 'easter.png'
        color = '#EF7041'
    elif datetime.utcnow().month == 10 and datetime.utcnow().day >= 15:
        icon = 'halloween.png'
        color = '#9A9A95'
    elif datetime.utcnow().month == 12 and datetime.utcnow().day >= 10:
        icon = 'xmas.png'
        color = '#790415'

    icon = icon
    color = color
