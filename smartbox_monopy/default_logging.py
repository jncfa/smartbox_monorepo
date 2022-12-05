
# TODO: Change fileConfig to dictConfig to use the new API
LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': { 
        'consoleLogger': { 
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': { 
        '': {  # root logger
            'handlers': ['consoleLogger'],
            'level': 'WARNING',
            'propagate': False
        },
        'bluetooth': { 
            'handlers': ['consoleLogger'],
            'level': 'INFO',
            'propagate': False
        },
        'oximeter': {  
            'handlers': ['consoleLogger'],
            'level': 'DEBUG',
            'propagate': False
        },
        'worker-1': {  
            'handlers': ['consoleLogger'],
            'level': 'DEBUG',
            'propagate': False
        },  
        'worker-2': {  
            'handlers': ['consoleLogger'],
            'level': 'DEBUG',
            'propagate': False
        },
        'worker-3': {  
            'handlers': ['consoleLogger'],
            'level': 'DEBUG',
            'propagate': False
        },
        'worker-4': {  
            'handlers': ['consoleLogger'],
            'level': 'DEBUG',
            'propagate': False
        },
        'worker-5': {  
            'handlers': ['consoleLogger'],
            'level': 'DEBUG',
            'propagate': False
        },
    } 
}