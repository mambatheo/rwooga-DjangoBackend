from rest_framework import status
from products.models import ServiceCategory, Product, Feedback, CustomRequest
from .test_setup import TestSetup


class ServiceCategoryViewTest(TestSetup):
    
    def test_list_categories(self):
        """Anyone can list categories"""
        response = self.client.get(self.category_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_category_staff_only(self):
        """Only staff can create categories"""
        # Customer tries to create
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.category_url, {
            'name': 'New Category',
            'description': 'Test',
            'requires_dimensions': False,
            'requires_material': False,
            'pricing_type': 'custom'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Staff creates successfully
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.category_url, {
            'name': 'New Category',
            'description': 'Test',
            'requires_dimensions': False,
            'requires_material': False,
            'pricing_type': 'custom'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_3d_printing_category(self):
        """Test creating a 3D printing category with proper settings"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.category_url, {
            'name': '3D Printing',
            'description': '3D printing services',
            'requires_dimensions': True,
            'requires_material': True,
            'pricing_type': 'custom'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['requires_dimensions'])


class ProductViewTest(TestSetup):
    
    def setUp(self):
        super().setUp()
        # Create a 3D printing category that requires dimensions
        self.category_3d = ServiceCategory.objects.create(
            name='3D Printing',
            description='3D printing products',
            requires_dimensions=True,
            requires_material=True,
            pricing_type='custom'
        )
        # Create a design category that doesn't require dimensions
        self.category_design = ServiceCategory.objects.create(
            name='Graphic Design',
            description='Design services',
            requires_dimensions=False,
            requires_material=False,
            pricing_type='fixed'
        )
        self.product = Product.objects.create(
            category=self.category_3d,
            name='Test Product',
            short_description='desc',
            unit_price=10000,
            length=10,
            width=5,
            height=3,
            
            published=True
        )
    
    def test_list_products(self):
        """Anyone can list products"""
        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_3d_product_with_dimensions(self):
        """Staff can create 3D products with required dimensions"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.product_url, {
            'category': str(self.category_3d.id),
            'name': 'New 3D Product',
            'short_description': 'desc',
            'unit_price': 5000,
            'length': 15,
            'width': 10,
            'height': 5,
            
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_design_product_without_dimensions(self):
        """Staff can create design products without dimensions"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.product_url, {
            'category': str(self.category_design.id),
            'name': 'Logo Design',
            'short_description': 'Custom logo design',
            'unit_price': 20000
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_3d_product_without_dimensions_fails(self):
        """Creating 3D product without required dimensions should fail"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.product_url, {
            'category': str(self.category_3d.id),
            'name': 'Incomplete Product',
            'short_description': 'Missing dimensions'
            # Missing length, width, height
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_product_customer_forbidden(self):
        """Only staff can create products"""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.product_url, {
            'category': str(self.category_design.id),
            'name': 'New Product',
            'short_description': 'desc',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_publish_product_staff_only(self):
        """Only staff can publish products"""
        url = f'{self.product_url}{self.product.id}/publish/'
        
        # Customer cannot publish
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Staff can publish
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_category(self):
        """Test category filtering"""
        response = self.client.get(f'{self.product_url}?category={self.category_3d.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_product_volume_in_response(self):
        """Test that product volume is calculated correctly in API response"""
        response = self.client.get(f'{self.product_url}{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_volume'], 150)  # 10 * 5 * 3


class FeedbackViewTest(TestSetup):
    
    def setUp(self):
        super().setUp()
        category = ServiceCategory.objects.create(
            name='Test',
            description='Test'
        )
        self.product = Product.objects.create(
            category=category,
            name='Test Product',
            short_description='desc',
            length=1,
            width=1,
            height=1
        )
    
    def test_create_feedback_authenticated_user(self):
        """Authenticated users can create feedback"""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.feedback_url, {
            'product': str(self.product.id),
            'client_name': 'John Doe',
            'message': 'Great!',
            'rating': 5,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify user was set automatically
        self.assertEqual(response.data['user'], str(self.customer_user.id))
    
    def test_create_feedback_unauthenticated_fails(self):
        """Unauthenticated users cannot create feedback"""
        response = self.client.post(self.feedback_url, {
            'product': str(self.product.id),
            'client_name': 'John Doe',
            'message': 'Great!',
            'rating': 5,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unpublished_feedback_hidden_from_customers(self):
        """Customers only see published feedback"""
        # Create unpublished feedback
        Feedback.objects.create(
            product=self.product,
            client_name='Test',
            message='Test',
            rating=5,
            published=False,
            user=self.customer_user
        )
        
        # Customer cannot see it
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.feedback_url)
        self.assertEqual(len(response.data['results']), 0)
        
        # Staff can see it
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.feedback_url)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_moderate_feedback_staff_only(self):
        """Only staff can moderate (publish/unpublish) feedback"""
        feedback = Feedback.objects.create(
            product=self.product,
            client_name='Test',
            message='Test',
            rating=5,
            published=False,
            user=self.customer_user
        )
        
        url = f'{self.feedback_url}{feedback.id}/moderate/'
        
        # Customer cannot moderate
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Staff can moderate
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['published'])


class CustomRequestViewTest(TestSetup):
    
    def test_create_custom_request_anyone(self):
        """Anyone can create custom request"""
        response = self.client.post(self.custom_request_url, {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'client_phone': '+250788123456',
            'title': 'Custom Request',
            'description': 'I need something custom'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_custom_request_with_category(self):
        """Custom request can be linked to a service category"""
        category = ServiceCategory.objects.create(
            name='3D Printing',
            description='3D printing services'
        )
        response = self.client.post(self.custom_request_url, {
            'client_name': 'Jane Doe',
            'client_email': 'jane@test.com',
            'client_phone': '+250788123456',
            'title': 'Custom 3D Model',
            'description': 'I need a custom 3D printed figurine',
            'service_category': str(category.id),
            'budget': 50000
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['service_category'], str(category.id))
    
    def test_list_requests_staff_only(self):
        """Only staff can list all custom requests"""
        CustomRequest.objects.create(
            client_name='Test',
            client_email='test@test.com',
            client_phone='123',
            title='Test',
            description='Test'
        )
        
        # Customer cannot list
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.custom_request_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Staff can list
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.custom_request_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_update_status_staff_only(self):
        """Only staff can update request status"""
        custom_request = CustomRequest.objects.create(
            client_name='Test',
            client_email='test@test.com',
            client_phone='123',
            title='Test',
            description='Test'
        )
        
        url = f'{self.custom_request_url}{custom_request.id}/'
        
        # Staff can update
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(url, {'status': 'COMPLETED'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        custom_request.refresh_from_db()
        self.assertEqual(custom_request.status, 'COMPLETED')
    
    def test_update_status_invalid(self):
        """Invalid status should be rejected"""
        custom_request = CustomRequest.objects.create(
            client_name='Test',
            client_email='test@test.com',
            client_phone='123',
            title='Test',
            description='Test'
        )
        
        url = f'{self.custom_request_url}{custom_request.id}/'
        
        self.client.force_authenticate(user=self.staff_user)       
        response = self.client.patch(url, {'status': 'INVALID_STATUS_NAME'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)