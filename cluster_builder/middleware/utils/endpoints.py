ENDPOINTS = {
            'POST': {
                'endpoints': {
                    'GET_CREDITS': {
                        'endpoint': '/get_credits',
                        'required_vars': ['billing_account_id'],
                        'data':{
                            "credits": {
                                "billing_account_id": '{billing_account_id}'
                            }
                        },
                        'headers': {"Content-Type": "application/json", "Accept": "application/json"}
                    },

                    'CREATE_ORDER': {
                        'endpoint': '/create_order',
                        'required_vars': ['billing_account_id'],
                        'data':{"order": {
                                "billing_account_id": '{billing_account_id}'
                            }
                        },
                        'headers': {"Content-Type": "application/json", "Accept": "application/json"}
                    },

                    'DELETE_ORDER': {
                        'endpoint': '/delete_order',
                        'required_vars': ['order_id'],
                        'data':{"order": {
                                "order_id": '{order_id}'
                            }
                        },
                        'headers': {"Content-Type": "application/json", "Accept": "application/json"}
                    },
                
                    'ADD_ORDER_TAG': {
                        'endpoint': '/add_order_tag',
                        'required_vars': ['order_id', 'tag_name', 'tag_value'],
                        'data':{"tag": {
                                "order_id": '{order_id}',
                                "tag_name": '{tag_name}',
                                "tag_value" : '{tag_value}'
                            }
                        },
                        'headers': {"Content-Type": "application/json", "Accept": "application/json"}
                    }
                    
                },
                'headers': {"Content-Type": "application/json", "Accept": "application/json"}
            }
}
