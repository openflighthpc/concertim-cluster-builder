"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Cluster Builder.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Visualisation App is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Visualisation App. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Cluster Builder, please visit:
 https://github.com/openflighthpc/concertim-cluster-builder
==============================================================================
"""

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
