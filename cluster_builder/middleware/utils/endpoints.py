ENDPOINTS = {
            'POST': {
                'endpoints': {
                    'GET_CREDITS': {
                        'endpoint': '/get_credits',
                        'required_vars': ['billing_account_id'],
                        'data':{"credits": {
                                "billing_account_id": '{billing_account_id}'
                            }
                        }
                    },
                    'headers': {"Content-Type": "application/json", "Accept": "application/json"}
            }
        }
}