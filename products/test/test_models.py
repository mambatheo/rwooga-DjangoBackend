from django.test import TestCase
from django.core.exceptions import ValidationError
from products.models import ServiceCategory, Product, ProductMedia, Feedback, CustomRequest
from django.contrib.auth import get_user_model

User = get_user_model()


class ServiceCategoryModelTest(TestCase):
    
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name='3D Printing',
            description='3D printing services',
            requires_dimensions=True,
            requires_material=True,
            pricing_type='per_unit'
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, '3D Printing')
        self.assertIsNotNone(self.category.slug)
        self.assertTrue(self.category.requires_dimensions)
        self.assertTrue(self.category.requires_material)
        self.assertEqual(self.category.pricing_type, 'per_unit')
    
    def test_category_str(self):
        self.assertEqual(str(self.category), '3D Printing')
    
    def test_slug_auto_generation(self):
        category = ServiceCategory.objects.create(
            name='Test Category',
            description='Test description'
        )
        self.assertEqual(category.slug, 'test-category')
    
    def test_category_defaults(self):
        """Test default values for new fields"""
        category = ServiceCategory.objects.create(
            name='Graphic Design',
            description='Design services'
        )
        self.assertFalse(category.requires_dimensions)
        self.assertFalse(category.requires_material)
        self.assertEqual(category.pricing_type, 'custom')


class ProductModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            full_name='Test User',
            phone_number='0788123456'
        )
        self.category = ServiceCategory.objects.create(
            name='3D Models',
            description='Test category',
            requires_dimensions=True,
            pricing_type='per_unit'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            short_description='Short desc',
            unit_price=10000,
            length=10,
            width=5,
            height=3,
            uploaded_by=self.user
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.unit_price, 10000)
    
    def test_product_volume_calculation(self):
        volume = self.product.product_volume
        self.assertEqual(volume, 150)  # 10 * 5 * 3
    
    def test_product_volume_with_missing_dimensions(self):
        """Test volume calculation when dimensions are None"""
        product = Product.objects.create(
            category=ServiceCategory.objects.create(
                name='Design Service',
                description='No dimensions needed'
            ),
            name='Design Product',
            short_description='desc'
        )
        self.assertIsNone(product.product_volume)
    
    def test_slug_auto_generation(self):
        self.assertEqual(self.product.slug, 'test-product')
    
    def test_product_str(self):
        self.assertEqual(str(self.product), 'Test Product')
    
    def test_validation_requires_dimensions_for_3d_category(self):
        """Products in categories requiring dimensions must have them"""
        product = Product(
            category=self.category,
            name='Incomplete Product',
            short_description='Missing dimensions'
            # No length, width, height
        )
        with self.assertRaises(ValidationError) as context:
            product.full_clean()
        
        self.assertIn('length', context.exception.message_dict)
        self.assertIn('width', context.exception.message_dict)
        self.assertIn('height', context.exception.message_dict)
    
    def test_no_dimension_validation_for_non_3d_category(self):
        """Products in categories not requiring dimensions can skip them"""
        design_category = ServiceCategory.objects.create(
            name='Graphic Design',
            description='Design services',
            requires_dimensions=False
        )
        product = Product(
            category=design_category,
            name='Logo Design',
            short_description='Custom logo'
            # No dimensions needed
        )
        # Should not raise ValidationError
        product.full_clean()
        product.save()
        self.assertIsNone(product.length)


class ProductMediaModelTest(TestCase):
    
    def setUp(self):
        category = ServiceCategory.objects.create(
            name='Test',
            description='Test'
        )
        self.product = Product.objects.create(
            category=category,
            name='Test Product',
            short_description='desc'
        )
    
    def test_product_media_str(self):
        """Test ProductMedia string representation"""
        media = ProductMedia.objects.create(
            product=self.product,
            display_order=1
        )
        expected = f"{self.product.name} - Media 1"
        self.assertEqual(str(media), expected)


class FeedbackModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            full_name='Test User',
            phone_number='0788123456'
        )
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
        self.feedback = Feedback.objects.create(
            product=self.product,
            client_name='John Doe',
            message='Great product!',
            rating=5,
            user=self.user
        )
    
    def test_feedback_creation(self):
        self.assertEqual(self.feedback.rating, 5)
        self.assertEqual(self.feedback.client_name, 'John Doe')
    
    def test_feedback_default_unpublished(self):
        self.assertFalse(self.feedback.published)


class CustomRequestModelTest(TestCase):
    
    def setUp(self):
        self.request = CustomRequest.objects.create(
            client_name='Jane Doe',
            client_email='jane@test.com',
            client_phone='+250788123456',
            title='Custom Design Request',
            description='I need a custom 3D model'
        )
    
    def test_custom_request_creation(self):
        self.assertEqual(self.request.client_name, 'Jane Doe')
        self.assertEqual(self.request.status, 'pending')
    
    def test_custom_request_str(self):
        self.assertEqual(str(self.request), 'Jane Doe - Custom Design Request')